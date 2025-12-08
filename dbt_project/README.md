# 📊 dbt Project - NYC Taxi Data Pipeline

Este subprojeto dbt gerencia as transformações SQL das camadas Silver e Gold do pipeline de dados NYC Taxi.

## 🎯 Visão Geral

O projeto dbt é responsável por:
- ✅ Criar e manter o schema da tabela Silver
- 📊 Gerar agregações e métricas da camada Gold
- 🧪 Executar testes de qualidade de dados
- 📚 Gerar documentação interativa do modelo de dados

## 📁 Estrutura do Projeto

```
dbt_project/
├── models/
│   ├── silver/                           # Camada Silver (dados refinados)
│   │   ├── nyc_trips_silver.sql         # Schema da tabela principal
│   │   └── schema.yml                   # Documentação e testes
│   │
│   └── gold/                            # Camada Gold (agregações)
│       ├── daily_trip_stats.sql         # Estatísticas diárias
│       ├── hourly_demand_patterns.sql   # Padrões de demanda horária
│       └── schema.yml                   # Documentação e testes
│
├── macros/                              # Macros Jinja customizadas
├── tests/                               # Testes SQL customizados
├── seeds/                               # Dados de referência (CSV)
│
├── dbt_project.yml                      # Configuração do projeto
├── profiles.yml                         # Configuração de conexão
├── run_dbt.sh                           # Script helper
└── README.md                            # Este arquivo
```

## 🗂️ Camadas de Dados

### 🥈 Silver Layer - Dados Refinados

#### `nyc_trips_silver`
Tabela principal com dados de viagens de táxi limpos e enriquecidos.

**Características:**
- Schema criado pelo dbt
- Dados inseridos pelo Spark transformer
- Inclui informações geográficas (boroughs, zones)
- Particionado por ano e mês
- Validado por testes de qualidade

**Colunas principais:**
- `VendorID`, `tpep_pickup_datetime`, `tpep_dropoff_datetime`
- `passenger_count`, `trip_distance`, `total_amount`
- `pickup_borough`, `pickup_zone`, `dropoff_borough`, `dropoff_zone`
- `partition_year`, `partition_month`, `processing_ts`

### 🥇 Gold Layer - Agregações e Métricas

#### `daily_trip_stats`
Estatísticas diárias agregadas por borough.

**Métricas:**
- Total de viagens
- Distância média
- Valor médio por viagem
- Receita total
- Número médio de passageiros

#### `hourly_demand_patterns`
Padrões de demanda por hora do dia e dia da semana.

**Métricas:**
- Viagens por hora
- Viagens por dia da semana
- Distância média por período
- Valor médio por período

## 🚀 Comandos Úteis

### Setup Inicial

```bash
# Entrar no container do Airflow
docker exec -it airflow bash

# Navegar para o projeto dbt
cd /opt/airflow/dbt_project

# Configurar variável de ambiente
export DBT_PROFILES_DIR=/opt/airflow/dbt_project

# Testar conexão com o banco
dbt debug --profiles-dir $DBT_PROFILES_DIR --project-dir .
```

### Executar Modelos

```bash
# Executar todos os modelos
dbt run --profiles-dir $DBT_PROFILES_DIR --project-dir .

# Executar apenas a camada silver
dbt run --select silver --profiles-dir $DBT_PROFILES_DIR --project-dir .

# Executar apenas a camada gold
dbt run --select gold --profiles-dir $DBT_PROFILES_DIR --project-dir .

# Executar um modelo específico
dbt run --select nyc_trips_silver --profiles-dir $DBT_PROFILES_DIR --project-dir .

# Executar com full-refresh (recriar tabelas)
dbt run --full-refresh --profiles-dir $DBT_PROFILES_DIR --project-dir .
```

### Testes de Qualidade

```bash
# Executar todos os testes
dbt test --profiles-dir $DBT_PROFILES_DIR --project-dir .

# Testar apenas a camada silver
dbt test --select silver --profiles-dir $DBT_PROFILES_DIR --project-dir .

# Testar apenas a camada gold
dbt test --select gold --profiles-dir $DBT_PROFILES_DIR --project-dir .

# Testar um modelo específico
dbt test --select nyc_trips_silver --profiles-dir $DBT_PROFILES_DIR --project-dir .
```

### Documentação

```bash
# Gerar documentação
dbt docs generate --profiles-dir $DBT_PROFILES_DIR --project-dir .

# Servir documentação (acessível em http://localhost:8001)
dbt docs serve --port 8001 --profiles-dir $DBT_PROFILES_DIR --project-dir .
```

### Outros Comandos

```bash
# Compilar modelos sem executar
dbt compile --profiles-dir $DBT_PROFILES_DIR --project-dir .

# Listar modelos
dbt list --profiles-dir $DBT_PROFILES_DIR --project-dir .

# Listar recursos (modelos, testes, seeds)
dbt ls --resource-type model --profiles-dir $DBT_PROFILES_DIR --project-dir .

# Ver lineage de um modelo
dbt run-operation graph --args '{model: nyc_trips_silver}'
```

## 🔧 Configuração

### Conexão com Banco de Dados

As credenciais são lidas das variáveis de ambiente (arquivo `.env`):

```env
NYC_POSTGRES_HOST=postgres-nyc-taxi
NYC_POSTGRES_PORT=5432
NYC_POSTGRES_USER=nyc_user
NYC_POSTGRES_PASSWORD=nyc_pass_123
NYC_POSTGRES_DB=nyc_taxi_db
```

### Profiles.yml

```yaml
nyc_taxi_dbt:
  outputs:
    dev:
      type: postgres
      host: "{{ env_var('NYC_POSTGRES_HOST') }}"
      port: "{{ env_var('NYC_POSTGRES_PORT') | int }}"
      user: "{{ env_var('NYC_POSTGRES_USER') }}"
      password: "{{ env_var('NYC_POSTGRES_PASSWORD') }}"
      dbname: "{{ env_var('NYC_POSTGRES_DB') }}"
      schema: public
      threads: 4
      keepalives_idle: 0
  target: dev
```

## 🔄 Integração com Airflow

Os modelos dbt são executados automaticamente pela DAG `nyc_taxi_data_pipeline` usando `BashOperator`:

```python
dbt_silver_task = BashOperator(
    task_id="dbt_create_silver_schema",
    bash_command="""
    cd /opt/airflow/dbt_project && \
    export DBT_PROFILES_DIR=/opt/airflow/dbt_project && \
    dbt run --select silver --profiles-dir $DBT_PROFILES_DIR --project-dir .
    """
)
```

## 📊 Workflow do Pipeline

```
1. Ingestão (Bronze)
   └─> Scripts Python carregam dados raw no MinIO
       │
2. dbt: Create Silver Schema
   └─> dbt cria estrutura da tabela nyc_trips_silver
       │
3. Transformação (Silver)
   └─> Spark processa e carrega dados no PostgreSQL
       │
4. dbt: Create Gold Models
   └─> dbt cria agregações a partir do Silver
       │
5. dbt: Test Quality
   └─> dbt valida qualidade dos dados
       │
6. dbt: Generate Docs
   └─> dbt gera documentação interativa
```

## 🧪 Testes Implementados

### Testes na Camada Silver

- ✅ `trip_id` é único
- ✅ `trip_id` não é nulo
- ✅ `tpep_pickup_datetime` não é nulo
- ✅ `trip_distance` não é nulo
- ✅ `total_amount` não é nulo

### Testes na Camada Gold

- ✅ `trip_date` é único em `daily_trip_stats`
- ✅ Métricas não são nulas
- ✅ Valores numéricos são positivos

## 📚 Documentação Gerada

O dbt gera documentação interativa que inclui:

- 📊 **Lineage Graphs**: Visualização de dependências entre modelos
- 📝 **Descrições**: Documentação de tabelas e colunas
- 🧪 **Testes**: Status e resultados dos testes
- 📈 **Métricas**: Estatísticas sobre os modelos
- 🔍 **SQL Compilado**: SQL final executado no banco

Para acessar:
1. Execute `dbt docs generate`
2. Execute `dbt docs serve --port 8001`
3. Acesse http://localhost:8001

## 🐛 Troubleshooting

### Erro de Conexão

```bash
# Verificar variáveis de ambiente
echo $NYC_POSTGRES_HOST
echo $NYC_POSTGRES_USER

# Testar conexão diretamente
psql -h postgres-nyc-taxi -U nyc_user -d nyc_taxi_db
```

### Modelos Falhando

```bash
# Ver logs detalhados
dbt run --select model_name --debug

# Compilar SQL sem executar
dbt compile --select model_name
```

### Limpar Cache

```bash
# Limpar arquivos compilados
rm -rf target/

# Limpar e recompilar
dbt clean
dbt compile
```

## 📖 Referências

- [dbt Documentation](https://docs.getdbt.com/)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [dbt Discourse Community](https://discourse.getdbt.com/)

---

Para mais informações sobre o pipeline completo, consulte o [README principal](../README.md).
