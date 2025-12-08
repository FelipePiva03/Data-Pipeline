# Quick Start - NYC Taxi Data Pipeline

## Configuração Atual da DAG

✅ **Período de Dados**: Maio 2025 até Outubro 2025
✅ **Total de Meses**: 6 meses
✅ **Tamanho Estimado**: ~400 MB de dados brutos
✅ **Execuções Paralelas**: Máximo 2

## Dados Disponíveis (Verificado)

```
2025: Mai, Jun, Jul, Ago, Set, Out (6 meses)
```

✅ Todos os 6 meses estão disponíveis e verificados.

💡 **Nota**: Se precisar de mais dados históricos, todos os meses de 2024 e início de 2025 também estão disponíveis. Basta ajustar a `start_date` na DAG.

## Passo a Passo para Executar

### 1. Iniciar os Containers

```bash
# Navegar para o diretório do projeto
cd "Data Pipeline"

# Iniciar todos os serviços
docker compose up -d --build

# Verificar se todos estão rodando
docker compose ps
```

**Aguarde ~2-3 minutos** para todos os serviços iniciarem.

### 2. Verificar Logs do Airflow

```bash
docker compose logs -f airflow
```

Aguarde até ver a mensagem "Airflow is ready" ou similar, depois pressione `Ctrl+C`.

### 3. Obter Senha do Airflow

```bash
docker exec airflow cat /opt/airflow/standalone_admin_password.txt
```

Copie a senha exibida.

### 4. Acessar Airflow UI

1. Abra seu navegador em: http://localhost:8080
2. Login:
   - **Username**: `admin`
   - **Password**: (senha obtida no passo 3)

### 5. Ativar e Executar a DAG

1. Na lista de DAGs, localize **`nyc_taxi_data_pipeline`**
2. Clique no **toggle (switch)** à esquerda para ativar a DAG
3. O Airflow automaticamente iniciará o processamento dos 6 meses
4. Você verá 2 execuções rodando em paralelo

### 6. Monitorar a Execução

- **Grid View**: Veja todas as 6 runs mensais
- **Graph View**: Veja o progresso de cada task individual
- **Logs**: Clique em cada task para ver logs detalhados

### 7. Acompanhar Progresso

```bash
# Ver status geral
docker exec airflow airflow dags list-runs -d nyc_taxi_data_pipeline

# Ver logs em tempo real
docker compose logs -f airflow | grep -E "ingest|transform|dbt"

# Verificar dados no MinIO
# Acesse: http://localhost:9001
# Login: minioadmin / minio@1234!
```

### 8. Consultar Dados Processados

```bash
# Conectar ao PostgreSQL
docker exec -it postgres-nyc-taxi psql -U nyc_user -d nyc_taxi_db

# Ver tabelas criadas
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

# Sair
\q
```

## Tempo Estimado de Execução

Com 3 runs paralelas:

- **Ingestão**: ~5 min/mês → ~37 min total
- **Transformação Spark**: ~10 min/mês → ~73 min total
- **dbt Silver**: ~1 min/mês → ~7 min total
- **dbt Gold**: ~2 min/mês → ~15 min total
- **dbt Tests**: ~1 min/mês → ~7 min total

**Total Estimado**: ~2-3 horas para processar todos os 22 meses

## Comandos Úteis Durante a Execução

### Pausar Temporariamente

```bash
# Pausar a DAG (para todas as novas execuções)
docker exec airflow airflow dags pause nyc_taxi_data_pipeline

# Despausar
docker exec airflow airflow dags unpause nyc_taxi_data_pipeline
```

### Verificar Espaço em Disco

```bash
# Ver tamanho dos dados no PostgreSQL
docker exec -it postgres-nyc-taxi psql -U nyc_user -d nyc_taxi_db -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname IN ('public', 'gold')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Ver uso de disco dos containers
docker system df -v
```

### Em Caso de Erro

```bash
# Ver logs de erro
docker compose logs airflow | grep -i error

# Reiniciar um serviço específico
docker compose restart airflow
docker compose restart postgres-nyc-taxi

# Limpar e recomeçar (CUIDADO: apaga todos os dados!)
docker compose down -v
docker compose up -d --build
```

## Acessar Documentação do dbt

Após as runs completarem:

```bash
# Entrar no container do Airflow
docker exec -it airflow bash

# Navegar para dbt
cd /opt/airflow/dbt_project

# Servir documentação
export DBT_PROFILES_DIR=/opt/airflow/dbt_project
dbt docs serve --port 8001

# Sair do container (Ctrl+D)
```

Acesse: http://localhost:8001

## Validar Resultados

### Verificar Quantidade de Dados

```sql
-- Conectar ao banco
docker exec -it postgres-nyc-taxi psql -U nyc_user -d nyc_taxi_db

-- Verificar total de viagens por mês
SELECT
    partition_year || '-' || LPAD(partition_month::text, 2, '0') as year_month,
    COUNT(*) as trips,
    pg_size_pretty(pg_total_relation_size('nyc_trips_silver')) as table_size
FROM nyc_trips_silver
GROUP BY partition_year, partition_month
ORDER BY partition_year, partition_month;

-- Verificar se todos os 22 meses foram processados
SELECT COUNT(DISTINCT (partition_year, partition_month)) as months_processed
FROM nyc_trips_silver;
-- Deve retornar: 22
```

### Verificar Qualidade dos Dados

Os testes dbt já validam automaticamente:
- ✅ trip_id é único e não-nulo
- ✅ tpep_pickup_datetime não é nulo
- ✅ trip_distance não é nulo
- ✅ total_amount não é nulo

Verifique os resultados na UI do Airflow na task `dbt_test_data_quality`.

## Próximos Passos

Após a conclusão bem-sucedida:

1. ✅ **Dados Bronze**: Armazenados no MinIO
2. ✅ **Dados Silver**: Tabela `nyc_trips_silver` no PostgreSQL
3. ✅ **Dados Gold**: Tabelas `daily_trip_stats` e `hourly_demand_patterns`
4. ✅ **Documentação**: Gerada pelo dbt
5. ✅ **Qualidade**: Validada pelos testes dbt

Você pode:
- Criar novos modelos dbt em `dbt_project/models/gold/`
- Adicionar mais testes em `schema.yml`
- Criar dashboards conectando ferramentas de BI ao PostgreSQL
- Ajustar a frequência da DAG (mensal, semanal, etc.)

## Troubleshooting

### "No space left on device"
- Libere espaço em disco
- Ou reduza o período processando menos meses

### "Connection refused" ao acessar PostgreSQL
```bash
docker compose logs postgres-nyc-taxi
docker compose restart postgres-nyc-taxi
```

### Tasks falhando com "Out of Memory"
- Aumente memória do Docker Desktop (Settings → Resources)
- Ou reduza `max_active_runs` para 1 ou 2

### Dados não aparecem no PostgreSQL
- Verifique se a task `transform_data` completou com sucesso
- Verifique logs: `docker compose logs airflow | grep transformer`

## Contatos e Suporte

- **Documentação dbt**: https://docs.getdbt.com
- **Documentação Airflow**: https://airflow.apache.org/docs
- **NYC TLC Data**: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
