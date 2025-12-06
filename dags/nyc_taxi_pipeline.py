from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="nyc_taxi_data_pipeline",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule_interval="@monthly",
    catchup=False,
    doc_md="""
    # NYC Taxi Data Pipeline

    Este DAG orquestra um pipeline de dados de ponta a ponta para os dados de táxi de NYC.
    
    - **Etapa de Ingestão**: Baixa os dados de viagens e zonas do site do TLC e os carrega em um bucket MinIO (camada bronze).
    - **Etapa de Transformação**: Lê os dados brutos do MinIO, aplica transformações usando PySpark para enriquecer os dados (joins, limpeza) e os salva em um banco de dados PostgreSQL (camada silver).
    
    A execução é parametrizada pelo mês e ano da partição de dados do Airflow.
    """,
    tags=["nyc-taxi", "data-pipeline", "spark", "postgres"],
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
        ### Tarefa de Transformação
        
        Executa o script `transformer.py` para processar os dados do mês corrente.
        - **Entrada**: Arquivos brutos da camada bronze (MinIO).
        - **Processamento**: Usa Spark para unir, limpar e enriquecer os dados.
        - **Saída**: Tabela `nyc_taxi_trips` populada na camada silver (PostgreSQL).
        """
    )

    # Define a ordem de execução das tarefas
    ingest_task >> transform_task
