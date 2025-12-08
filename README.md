# 🚕 NYC Taxi Data Pipeline

![Python](https://img.shields.io/badge/python-3.11-blue)
![Airflow](https://img.shields.io/badge/airflow-2.9.1-green)
![Spark](https://img.shields.io/badge/spark-3.5-orange)
![dbt](https://img.shields.io/badge/dbt-1.7-red)
![Docker](https://img.shields.io/badge/docker-compose-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Pipeline de dados completo de ponta a ponta para análise dos dados de táxi de NYC (New York City Taxi and Limousine Commission). Implementa a arquitetura Medallion (Bronze → Silver → Gold) orquestrada com Apache Airflow.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Stack Tecnológica](#stack-tecnológica)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Como Usar](#como-usar)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Pipeline de Dados](#pipeline-de-dados)
- [Comandos Úteis](#comandos-úteis)
- [Dashboard](#dashboard)
- [Contribuindo](#contribuindo)
- [Licença](#licença)
- [Autor](#autor)

## 🎯 Visão Geral

Este projeto demonstra a construção de um data pipeline moderno e escalável utilizando as principais ferramentas do ecossistema de engenharia de dados:

- **Ingestão automatizada** de dados públicos do NYC TLC
- **Processamento distribuído** com Apache Spark para grandes volumes
- **Transformações SQL** modulares e testáveis com dbt
- **Orquestração** robusta com Apache Airflow
- **Armazenamento** em camadas (Data Lake + Data Warehouse)
- **Visualização** interativa com Streamlit

### Arquitetura Medallion

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Source    │────▶│    Bronze    │────▶│    Silver    │────▶│     Gold     │
│  (NYC TLC)  │     │   (MinIO)    │     │ (PostgreSQL) │     │ (PostgreSQL) │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
  Public API         Raw Data Layer     Clean & Enriched    Aggregated Metrics
```

- **Bronze (Raw)**: Dados brutos, exatamente como extraídos da fonte
- **Silver (Refined)**: Dados limpos, validados, enriquecidos e normalizados
- **Gold (Curated)**: Dados agregados e otimizados para análise e BI

## 🏗️ Arquitetura

### Containers

O ambiente completo roda em containers Docker:

| Container | Descrição | Porta | Acesso |
|-----------|-----------|-------|--------|
| **airflow** | Apache Airflow (orquestrador) | `8080` | http://localhost:8080 |
| **postgres-airflow** | PostgreSQL (metadados Airflow) | `5432` | Interno |
| **postgres-nyc-taxi** | PostgreSQL (Data Warehouse) | `5433` | localhost:5433 |
| **minio** | MinIO (Data Lake S3-compatible) | `9000`, `9001` | http://localhost:9001 |
| **streamlit** | Dashboard interativo | `8501` | http://localhost:8501 |

### Acessos Rápidos

- **Airflow UI**: http://localhost:8080
  - User: `admin`
  - Password: `docker exec airflow cat /opt/airflow/standalone_admin_password.txt`
- **MinIO Console**: http://localhost:9001
  - User: `minioadmin`
  - Password: `minio@1234!`
- **Streamlit Dashboard**: http://localhost:8501
- **PostgreSQL**: `localhost:5433`
  - Database: `nyc_taxi_db`
  - User: `nyc_user`
  - Password: `nyc_pass_123`

## 🛠️ Stack Tecnológica

- **Orquestração**: Apache Airflow 2.9.1
- **Processamento**: Apache Spark 3.5 (PySpark)
- **Transformação**: dbt 1.7 (data build tool)
- **Data Lake**: MinIO (S3-compatible storage)
- **Data Warehouse**: PostgreSQL 15
- **Visualização**: Streamlit
- **Containerização**: Docker & Docker Compose
- **Linguagem**: Python 3.11

## 📦 Pré-requisitos

- **Docker**: versão 20.10 ou superior
- **Docker Compose**: versão 2.0 ou superior
- **Recursos mínimos**:
  - 8GB RAM disponível para Docker
  - 10GB espaço em disco livre
  - 4 CPU cores (recomendado)

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/FelipePiva03/Data-Pipeline.git
cd Data-Pipeline
```

### 2. Configure as variáveis de ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# (Opcional) Edite o .env para customizar credenciais
nano .env
```

⚠️ **Importante**: Para produção, altere as senhas padrão!

### 3. Inicie os containers

```bash
# Build e start de todos os serviços
docker compose up -d --build

# Verificar se todos estão rodando
docker compose ps
```

Aguarde ~2-3 minutos para todos os serviços iniciarem.

### 4. Verifique a inicialização

```bash
# Acompanhar logs do Airflow
docker compose logs -f airflow

# Pressione Ctrl+C quando ver "Airflow is ready"
```

## 💡 Como Usar

### Quick Start

1. **Obtenha a senha do Airflow**:
```bash
docker exec airflow cat /opt/airflow/standalone_admin_password.txt
```

2. **Acesse a UI do Airflow**: http://localhost:8080
   - Login com `admin` e a senha obtida

3. **Execute a DAG**:
   - Localize `nyc_taxi_data_pipeline`
   - Ative a DAG (toggle à esquerda)
   - Clique em "Trigger DAG"
   - Acompanhe no Graph View

4. **Acesse o Dashboard**: http://localhost:8501

### Consultar Dados Processados

```bash
# Conectar ao PostgreSQL
docker exec -it postgres-nyc-taxi psql -U nyc_user -d nyc_taxi_db

# Ver tabelas
\dt

# Consultar dados Silver
SELECT
    partition_year,
    partition_month,
    COUNT(*) as total_trips,
    ROUND(AVG(trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare
FROM nyc_trips_silver
GROUP BY partition_year, partition_month
ORDER BY partition_year, partition_month;

# Consultar agregações Gold
SELECT * FROM daily_trip_stats ORDER BY trip_date DESC LIMIT 20;
```

## 📁 Estrutura do Projeto

```
Data-Pipeline/
├── dags/
│   └── nyc_taxi_pipeline.py          # DAG principal do Airflow
│
├── dbt_project/                      # Transformações SQL com dbt
│   ├── models/
│   │   ├── silver/                   # Camada Silver (limpeza)
│   │   └── gold/                     # Camada Gold (agregações)
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── README.md
│
├── scripts/                          # Scripts Python do pipeline
│   ├── ingestor.py                   # Bronze: Ingestão de dados
│   ├── transformer.py                # Silver: Transformação Spark
│   ├── init_dbt.py                   # Setup do dbt
│   └── utils/
│       ├── logger.py                 # Configuração de logs
│       └── spark_session.py          # Spark session builder
│
├── streamlit_app/                    # Dashboard interativo
│   ├── app.py                        # Aplicação Streamlit
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── spark-jars/                       # JARs para Spark
│   ├── postgresql-42.6.0.jar
│   ├── hadoop-aws-3.4.1.jar
│   └── ...
│
├── .env.example                      # Exemplo de variáveis de ambiente
├── .gitignore
├── docker-compose.yml                # Orquestração dos serviços
├── Dockerfile                        # Imagem customizada Airflow
├── LICENSE                           # Licença MIT
├── requirements.txt                  # Dependências Python
├── README.md                         # Este arquivo
├── QUICK_START.md                    # Guia rápido
└── EXECUTION_GUIDE.md                # Guia detalhado de execução
```

## 🔄 Pipeline de Dados

### Fluxo de Execução

```
┌──────────────────┐
│ 1. Ingest Data   │  Download dos dados → MinIO (Bronze)
└────────┬─────────┘
         │
         ▼
┌─────────────────────────┐
│ 2. dbt: Create Silver   │  Criar schema da tabela Silver
└────────┬────────────────┘
         │
         ▼
┌──────────────────────┐
│ 3. Transform Data    │  Spark: Limpar e enriquecer → PostgreSQL
└────────┬─────────────┘
         │
         ▼
┌────────────────────────┐
│ 4. dbt: Create Gold    │  Criar agregações (Gold)
└────────┬───────────────┘
         │
         ▼
┌──────────────────────────┐
│ 5. dbt: Test Quality     │  Executar testes de qualidade
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ 6. dbt: Generate Docs    │  Gerar documentação
└──────────────────────────┘
```

### Detalhes das Camadas

#### 🥉 Bronze Layer - Ingestão ([ingestor.py](scripts/ingestor.py))
- **Fonte**: [NYC Taxi & Limousine Commission](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
- **Dados**: Yellow Taxi Trip Records (Parquet) + Zone Lookup (CSV)
- **Destino**: MinIO bucket `ingestion-data-lake/bronze/`
- **Características**: Dados imutáveis, particionados por ano/mês

#### 🥈 Silver Layer - Transformação ([transformer.py](scripts/transformer.py))
- **Processamento**: PySpark com otimizações
- **Operações**:
  - Validação de tipos e formatos
  - Filtros de qualidade (distância > 0, valores > 0)
  - Enriquecimento com dados geográficos (boroughs, zones)
  - Adição de metadados (timestamp de processamento)
- **Destino**: PostgreSQL `nyc_trips_silver`

#### 🥇 Gold Layer - Agregações (dbt)
- **Modelos**:
  - `daily_trip_stats`: Estatísticas diárias por borough
  - `hourly_demand_patterns`: Padrões de demanda por hora/dia da semana
- **Features**: Incrementais, testados, documentados
- **Destino**: PostgreSQL schema `public`

## 🎨 Dashboard

O projeto inclui um dashboard interativo desenvolvido com Streamlit que permite:

- 📊 Visualizar métricas principais (viagens, receita, distância)
- 📈 Analisar tendências temporais
- 🗺️ Explorar rotas populares
- 💰 Acompanhar receita e gorjetas
- 🏙️ Comparar performance por bairro
- ⏰ Identificar padrões de demanda

Acesse em: http://localhost:8501

## 🛠️ Comandos Úteis

### Docker

```bash
# Parar todos os containers
docker compose down

# Parar e remover volumes (CUIDADO: apaga dados!)
docker compose down -v

# Restart de um serviço específico
docker compose restart airflow

# Ver logs
docker compose logs -f airflow
docker compose logs -f streamlit

# Verificar recursos
docker stats
```

### Airflow CLI

```bash
# Listar DAGs
docker exec airflow airflow dags list

# Listar runs
docker exec airflow airflow dags list-runs -d nyc_taxi_data_pipeline

# Testar uma task
docker exec airflow airflow tasks test nyc_taxi_data_pipeline ingest_data 2025-05-01

# Pausar/Despausar DAG
docker exec airflow airflow dags pause nyc_taxi_data_pipeline
docker exec airflow airflow dags unpause nyc_taxi_data_pipeline
```

### dbt

```bash
# Entrar no container
docker exec -it airflow bash

# Navegar para o projeto
cd /opt/airflow/dbt_project

# Configurar ambiente
export DBT_PROFILES_DIR=/opt/airflow/dbt_project

# Executar modelos
dbt run --select silver
dbt run --select gold

# Executar testes
dbt test

# Gerar e servir documentação
dbt docs generate
dbt docs serve --port 8001
```

### PostgreSQL

```bash
# Conectar ao banco
docker exec -it postgres-nyc-taxi psql -U nyc_user -d nyc_taxi_db

# Ver tamanho das tabelas
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname IN ('public')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Sair
\q
```

## 👤 Autor

**Felipe Piva**

- GitHub: [@FelipePiva03](https://github.com/FelipePiva03)
- LinkedIn: [Felipe Piva](https://linkedin.com/in/felipe-piva-developer)
- Email: felipepiva02@gmail.com

## 📚 Referências

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [dbt Documentation](https://docs.getdbt.com/)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

---

⭐ Se este projeto foi útil, considere dar uma estrela!
