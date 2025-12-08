# Guia de Execução da DAG NYC Taxi

## Configuração Atual

- **Data de início**: 2025-05-01
- **Data de término**: 2025-10-31
- **Schedule**: Mensal (`@monthly`)
- **Catchup**: Ativado
- **Max runs paralelas**: 2

Isso significa que ao ativar a DAG, ela processará **os últimos 6 meses de 2025** (maio a outubro).

## ⚠️ Pré-requisitos

Antes de executar a DAG, certifique-se de que:

1. ✅ **JARs do Spark foram baixados**
   ```bash
   cd spark-jars
   ./download_jars.sh
   cd ..
   ```
   📋 Veja detalhes em [spark-jars/README.md](spark-jars/README.md)

2. ✅ **Todos os containers estão rodando**
   ```bash
   docker compose ps
   ```
   Deve mostrar: airflow, postgres-airflow, postgres-nyc-taxi, minio, streamlit

3. ✅ **Dashboard Streamlit está acessível**
   - Acesse: http://localhost:8501

## Opções de Execução

### Opção 1: Processar Todos os Meses (Padrão Atual)

Simplesmente ative a DAG na UI do Airflow. Ela processará automaticamente:
- 2025-05 (Maio)
- 2025-06 (Junho)
- 2025-07 (Julho)
- 2025-08 (Agosto)
- 2025-09 (Setembro)
- 2025-10 (Outubro)
- **Total**: 6 meses

**Tempo estimado**: ~1 hora (com 2 runs paralelas)

**Acompanhar progresso**:
- 🎯 Airflow UI: http://localhost:8080
- 📊 Streamlit Dashboard: http://localhost:8501 (atualiza automaticamente)
- 🗄️ MinIO Console: http://localhost:9001

### Opção 2: Processar Apenas Alguns Meses

Se você quiser processar apenas meses específicos:

1. **Via UI do Airflow**:
   - Vá para a DAG `nyc_taxi_data_pipeline`
   - Clique em "Browse" → "DAG Runs"
   - Clique em "Clear" nas runs que você NÃO quer executar
   - Isso marcará elas como "success" sem executar

2. **Via CLI**:
   ```bash
   # Processar apenas maio de 2025
   docker exec airflow airflow dags backfill \
       -s 2025-05-01 \
       -e 2025-05-31 \
       nyc_taxi_data_pipeline
   ```

### Opção 3: Processar Apenas os Últimos N Meses

Modifique a `start_date` na DAG ([dags/nyc_taxi_pipeline.py](dags/nyc_taxi_pipeline.py)):

```python
# Para processar apenas 2024
start_date=pendulum.datetime(2024, 1, 1, tz="UTC")

# Para processar apenas últimos 6 meses
start_date=pendulum.now('UTC').subtract(months=6).start_of('month')

# Para processar apenas últimos 3 meses
start_date=pendulum.now('UTC').subtract(months=3).start_of('month')
```

### Opção 4: Executar Manualmente para Datas Específicas

1. Na UI do Airflow, vá para a DAG
2. Clique em "Trigger DAG"
3. Escolha "Trigger w/ config"
4. Configure a data de execução desejada

## Monitoramento

### Verificar Progresso

#### Via Airflow
```bash
# Ver status de todas as runs
docker exec airflow airflow dags list-runs -d nyc_taxi_data_pipeline

# Ver logs de uma task específica
docker compose logs -f airflow | grep "ingest_data"

# Ver logs do Streamlit
docker compose logs -f streamlit
```

#### Via Dashboard Streamlit
1. Acesse http://localhost:8501
2. Use os filtros para visualizar dados conforme são processados
3. Métricas são atualizadas em tempo real

#### Via PostgreSQL
```bash
# Verificar espaço em disco
docker exec postgres-nyc-taxi psql -U nyc_user -d nyc_taxi_db -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Contar registros processados
docker exec postgres-nyc-taxi psql -U nyc_user -d nyc_taxi_db -c "
SELECT COUNT(*) as total_trips FROM nyc_trips_silver;"
```

### Pausar Execução

Se precisar pausar:

```bash
# Pausar a DAG
docker exec airflow airflow dags pause nyc_taxi_data_pipeline

# Despausar
docker exec airflow airflow dags unpause nyc_taxi_data_pipeline
```

## Acompanhando no Streamlit

Enquanto a DAG executa, você pode:

1. **Visualizar dados em tempo real** no dashboard
2. **Filtrar por data** para ver apenas dados já processados
3. **Explorar métricas**:
   - Total de viagens
   - Receita gerada
   - Distância percorrida
   - Padrões de demanda
   - Rotas populares

**URL**: http://localhost:8501

## Troubleshooting

### Se as runs estiverem falhando

1. **Verificar logs do Airflow**:
   ```bash
   docker compose logs -f airflow
   ```

2. **Verificar se os JARs do Spark estão presentes**:
   ```bash
   ls -lh spark-jars/*.jar
   ```
   Deve listar: postgresql-42.6.0.jar, hadoop-aws-3.4.1.jar, aws-java-sdk-bundle-1.12.772.jar

3. **Verificar se MinIO tem espaço**:
   - Acesse http://localhost:9001
   - Login: `minioadmin` / `minio@1234!`
   - Verifique o bucket `ingestion-data-lake`

4. **Verificar se PostgreSQL está acessível**:
   ```bash
   docker exec -it postgres-nyc-taxi psql -U nyc_user -d nyc_taxi_db -c "SELECT 1;"
   ```

5. **Verificar memória do Spark**:
   ```bash
   docker stats airflow
   ```
   Se falhar com OutOfMemory, aumente memória do Docker (Settings → Resources)

### Dashboard Streamlit não mostra dados

```bash
# Verificar logs do Streamlit
docker compose logs streamlit

# Verificar se há dados no PostgreSQL
docker exec -it postgres-nyc-taxi psql -U nyc_user -d nyc_taxi_db -c "
SELECT COUNT(*) FROM nyc_trips_silver;"

# Reiniciar Streamlit
docker compose restart streamlit
```

### ClassNotFoundException ou erros de Spark

⚠️ **Causa**: JARs não foram baixados
**Solução**:
```bash
cd spark-jars
./download_jars.sh
cd ..
docker compose restart airflow
```

### Se quiser recomeçar do zero

```bash
# Parar containers
docker compose down

# Remover volumes (APAGA TODOS OS DADOS!)
docker compose down -v

# Baixar JARs novamente
cd spark-jars
./download_jars.sh
cd ..

# Reconstruir e iniciar
docker compose up -d --build
```

## Estimativas de Recursos

Para processar 6 meses de dados NYC Taxi (Mai-Out 2025):

- **Espaço em disco**: ~2-3 GB (dados brutos ~400 MB + processados)
- **RAM**: Mínimo 8 GB recomendado
- **Tempo**:
  - Ingestão: ~3-5 min por mês
  - Transformação: ~5-10 min por mês
  - dbt: ~1-2 min por mês
  - **Total**: ~10-17 min por mês × 6 meses = **1-1.5 horas**

Com 2 runs paralelas: **~30-60 minutos total**

## Recomendação

Para o primeiro teste, recomendo:

1. ✅ Processar apenas **1 mês** primeiro para validar (por exemplo, outubro)
2. ✅ Verificar dados no PostgreSQL e no Dashboard Streamlit
3. ✅ Confirmar que tudo está funcionando
4. ✅ Depois liberar para processar todos os 6 meses

Para testar com apenas 1 mês, modifique temporariamente a DAG:

```python
start_date=pendulum.datetime(2025, 10, 1, tz="UTC")  # Apenas outubro
end_date=pendulum.datetime(2025, 10, 31, tz="UTC")
```

**Expansão Futura**: Se precisar de mais dados históricos, ajuste:

```python
# Para processar todo 2024 e 2025
start_date=pendulum.datetime(2024, 1, 1, tz="UTC")
end_date=pendulum.datetime(2025, 10, 31, tz="UTC")
max_active_runs=3  # Aumentar paralelismo
```

## URLs Rápidas

- 🎯 **Airflow UI**: http://localhost:8080
- 📊 **Streamlit Dashboard**: http://localhost:8501
- 🗄️ **MinIO Console**: http://localhost:9001
- 📚 **dbt Docs**: http://localhost:8001 (após `dbt docs serve`)

## Próximos Passos

Após execução bem-sucedida:

1. ✅ Explore o **Dashboard Streamlit** com diferentes filtros
2. ✅ Consulte dados no **PostgreSQL** diretamente
3. ✅ Gere **documentação do dbt** (`dbt docs generate && dbt docs serve`)
4. ✅ Crie **novos modelos Gold** em `dbt_project/models/gold/`
5. ✅ Adicione **mais testes** em `dbt_project/models/*/schema.yml`
6. ✅ **Customize o dashboard** editando `streamlit_app/app.py`