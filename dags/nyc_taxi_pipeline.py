from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="nyc_taxi_data_pipeline",
    start_date=pendulum.datetime(2025, 5, 1, tz="UTC"),  # Últimos 6 meses (Mai-Out 2025)
    end_date=pendulum.datetime(2025, 10, 31, tz="UTC"),  # Até outubro de 2025
    schedule_interval="@monthly",
    catchup=True,
    max_active_runs=2,  # Limita execuções paralelas para não sobrecarregar
    doc_md="""
    # NYC Taxi Data Pipeline

    Este DAG orquestra um pipeline de dados de ponta a ponta para os dados de táxi de NYC.

    ## Pipeline Completo:
    1. **Bronze Layer - Ingestão**: Baixa os dados de viagens e zonas do site do TLC e os carrega em um bucket MinIO
    2. **Silver Layer - Transformação**: Usa PySpark para limpar e enriquecer os dados e os salva no PostgreSQL
    3. **Silver Layer - dbt**: Cria/atualiza schema das tabelas Silver usando dbt
    4. **Gold Layer - dbt**: Gera agregações e modelos analíticos usando dbt
    5. **Quality Assurance - dbt**: Executa testes de qualidade de dados

    A execução é parametrizada pelo mês e ano da partição de dados do Airflow.
    """,
    tags=["nyc-taxi", "data-pipeline", "spark", "postgres", "dbt"],
) as dag:
    
    # Scripts estão montados no diretório /opt/airflow/scripts
    base_command = "python /opt/airflow/scripts/"

    # O mês e ano são extraídos da data de execução lógica do Airflow
    # Formato: {{ data_interval_end.strftime('%Y') }} e {{ data_interval_end.strftime('%m') }}
    # Usamos data_interval_end para processar o mês que acabou de terminar.
    # Ex: para a run de @monthly de 1 de Fev, processamos os dados de Janeiro.
    year = "{{ data_interval_end.strftime('%Y') }}"
    month = "{{ data_interval_end.strftime('%m') }}"

    ingest_task = BashOperator(
        task_id="ingest_data",
        bash_command=f"{base_command}ingestor.py --year {year} --month {month}",
        doc_md="""
        ### Tarefa de Ingestão
        
        Executa o script `ingestor.py` para baixar os dados do mês corrente e
        armazená-los na camada bronze (MinIO).
        - **Entrada**: Ano e mês da execução.
        - **Saída**: Arquivos Parquet (viagens) e CSV (zonas) no bucket `ingestion-data-lake`.
        """
    )

    transform_task = BashOperator(
        task_id="transform_data",
        bash_command=f"{base_command}transformer.py --year {year} --month {month}",
        doc_md="""
        ### Tarefa de Transformação (Spark)

        Executa o script `transformer.py` para processar os dados do mês corrente.
        - **Entrada**: Arquivos brutos da camada bronze (MinIO).
        - **Processamento**: Usa Spark para unir, limpar e enriquecer os dados.
        - **Saída**: Dados inseridos na tabela `nyc_trips_silver` no PostgreSQL.
        """
    )

    # dbt: Create/Update Silver layer schema
    dbt_silver_task = BashOperator(
        task_id="dbt_create_silver_schema",
        bash_command="""
        cd /opt/airflow/dbt_project && \
        export DBT_PROFILES_DIR=/opt/airflow/dbt_project && \
        dbt run --select silver --profiles-dir $DBT_PROFILES_DIR --project-dir /opt/airflow/dbt_project
        """,
        doc_md="""
        ### dbt: Criar Schema Silver

        Executa modelos dbt da camada Silver para garantir que o schema está correto.
        - **Entrada**: Configuração dbt (models/silver).
        - **Processamento**: dbt cria/atualiza a estrutura da tabela `nyc_trips_silver`.
        - **Saída**: Schema da tabela Silver no PostgreSQL.

        **Nota**: Esta tarefa deve rodar ANTES da transformação Spark para garantir que a tabela existe.
        """
    )

    # dbt: Create Gold layer aggregations
    dbt_gold_task = BashOperator(
        task_id="dbt_create_gold_models",
        bash_command="""
        cd /opt/airflow/dbt_project && \
        export DBT_PROFILES_DIR=/opt/airflow/dbt_project && \
        dbt run --select gold --profiles-dir $DBT_PROFILES_DIR --project-dir /opt/airflow/dbt_project
        """,
        doc_md="""
        ### dbt: Criar Modelos Gold

        Executa modelos dbt da camada Gold para criar agregações e métricas.
        - **Entrada**: Dados da tabela `nyc_trips_silver`.
        - **Processamento**: dbt cria modelos agregados (daily_trip_stats, hourly_demand_patterns).
        - **Saída**: Tabelas Gold populadas no PostgreSQL.
        """
    )

    # dbt: Run tests
    dbt_test_task = BashOperator(
        task_id="dbt_test_data_quality",
        bash_command="""
        cd /opt/airflow/dbt_project && \
        export DBT_PROFILES_DIR=/opt/airflow/dbt_project && \
        dbt test --profiles-dir $DBT_PROFILES_DIR --project-dir /opt/airflow/dbt_project
        """,
        doc_md="""
        ### dbt: Testes de Qualidade

        Executa testes de qualidade de dados definidos nos schemas dbt.
        - **Testes**: not_null, unique, relacionamentos, etc.
        - **Saída**: Relatório de qualidade dos dados.

        Se algum teste falhar, a task falhará e alertará o time.
     1   """
    )

    # dbt: Generate documentation
    dbt_docs_task = BashOperator(
        task_id="dbt_generate_docs",
        bash_command="""
        cd /opt/airflow/dbt_project && \
        export DBT_PROFILES_DIR=/opt/airflow/dbt_project && \
        dbt docs generate --profiles-dir $DBT_PROFILES_DIR --project-dir /opt/airflow/dbt_project
        """,
        doc_md="""
        ### dbt: Gerar Documentação

        Gera documentação atualizada do modelo de dados.
        - **Saída**: Arquivos de documentação em /opt/airflow/dbt_project/target.

        A documentação pode ser visualizada com `dbt docs serve`.
        """
    )

    # Define a ordem de execução das tarefas
    # Pipeline flow:
    # 1. Ingest raw data to Bronze (MinIO)
    # 2. Create Silver schema with dbt (if not exists)
    # 3. Transform and load data to Silver with Spark
    # 4. Create Gold aggregations with dbt
    # 5. Run data quality tests with dbt
    # 6. Generate documentation with dbt

    ingest_task >> dbt_silver_task >> transform_task >> dbt_gold_task >> dbt_test_task >> dbt_docs_task
