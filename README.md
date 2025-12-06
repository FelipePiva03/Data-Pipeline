
# Projeto de Pipeline de Dados com Airflow, dbt e Spark

##  Visão Geral

Este projeto implementa um pipeline de dados orquestrado com Apache Airflow para ingestão, processamento e transformação de dados. Ele utiliza MinIO como Data Lake, Spark para processamento distribuído e dbt para transformações baseadas em SQL.

O ambiente de desenvolvimento e produção é totalmente containerizado com Docker.

## Arquitetura e Serviços

O ambiente é definido no arquivo `docker-compose.yml` e consiste nos seguintes serviços:

- **`airflow`**: O orquestrador central. A UI do Airflow fica disponível em `http://localhost:8080`.
  - **DAGs**: As definições de fluxo de trabalho do Airflow são montadas a partir da pasta local `./dags`.
  - **Scripts**: Scripts Python, como o de ingestão, estão na pasta `./scripts`.
  - **dbt**: O projeto dbt em `./dbt_project` é disponibilizado para o Airflow.
- **`postgres-airflow`**: O banco de dados PostgreSQL que serve como backend de metadados para o Airflow.
- **`minio`**: Um serviço de armazenamento de objetos compatível com a API do Amazon S3. Usado como nosso Data Lake.
  - A console do MinIO fica acessível em `http://localhost:9001` (login padrão: `minioadmin` / `minio@1234!`).
- **`minio_mc`**: Um container de inicialização que cria o bucket `landing` no MinIO na primeira execução.

## Pré-requisitos

- Docker
- Docker Compose

## Instalação e Execução

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd <nome-do-repositorio>
   ```

2. **Inicie os serviços com Docker Compose:**
   ```bash
   docker-compose up --build
   ```
   O comando `--build` garante que a imagem do Airflow seja construída com todas as dependências do `requirements.txt`.

3. **Acesse o Airflow:**
   - Abra seu navegador e acesse `http://localhost:8080`.
   - O login padrão do Airflow (na primeira vez) é `airflow` / `airflow`.

## Estrutura do Projeto

```
.
├── dags/                # Contém as DAGs do Airflow.
├── dbt_project/         # Projeto dbt com modelos, seeds, etc.
├── logs/                # Logs gerados pelo Airflow.
├── plugins/             # Plugins customizados do Airflow.
├── scripts/             # Scripts Python (ex: ingestão, processamento).
│   └── ingest.py
├── .env                 # Arquivo para variáveis de ambiente (não versionado).
├── docker-compose.yml   # Orquestração dos containers.
├── Dockerfile           # Definição da imagem Docker customizada para o Airflow.
└── requirements.txt     # Dependências Python.
```

## Detalhes do Pipeline

O pipeline foi desenhado para executar as seguintes etapas:

1.  **Ingestão (Extract)**: Uma DAG no Airflow aciona o script `scripts/ingest.py`. Este script baixa dados de uma fonte externa (ex: NYC Taxi Data) e os armazena no bucket `landing` do MinIO.
2.  **Processamento (Transform)**: Outra DAG utiliza PySpark para ler os dados brutos do Data Lake, realizar limpezas, agregações e outras transformações. O resultado é salvo em uma camada processada (ex: `processed`) no Data Lake.
3.  **Carregamento e Modelagem (Load & Transform)**: Uma DAG final orquestra a execução de modelos dbt. O dbt lê os dados da camada processada, aplica a lógica de modelagem de negócios e materializa as tabelas finais em um Data Warehouse (que poderia ser o próprio Postgres ou outro banco de dados).
