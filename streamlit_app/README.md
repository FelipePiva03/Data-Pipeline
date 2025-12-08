# 📊 NYC Taxi Dashboard - Streamlit

Dashboard interativo e em tempo real para visualização e análise dos dados do pipeline NYC Taxi.

## ✨ Características

### Métricas Principais
- 🚕 **Total de Viagens**: Contador de viagens no período selecionado
- 📏 **Distância Total e Média**: Análise de distâncias percorridas
- 💰 **Receita Total e Tarifa Média**: Métricas financeiras
- ⏱️ **Duração Média**: Tempo médio de viagem

### Visualizações Interativas

#### 📈 Viagens por Dia
- Gráfico de linha temporal
- Identificação de tendências e padrões

#### 🏙️ Top 10 Bairros (Pickup)
- Gráfico de barras interativo
- Colorido por receita média
- Comparação entre diferentes regiões

#### ⏰ Padrão de Demanda por Hora
- Distribuição de viagens ao longo do dia
- Identificação de horários de pico

#### 💳 Métodos de Pagamento
- Gráfico de pizza com distribuição
- Categorização automática dos tipos

#### 🗺️ Top 10 Rotas Mais Populares
- Tabela detalhada com:
  - Bairro e zona de origem/destino
  - Número de viagens
  - Distância média
  - Tarifa média
  - Duração média

#### 💰 Análise de Receita
- Gráfico de linha duplo:
  - Receita total diária
  - Gorjetas diárias
- Comparação temporal

### Filtros Dinâmicos

- 📅 **Filtro de Data**: Selecione período de análise (início e fim)
- 🏙️ **Filtro de Bairros**: Selecione múltiplos bairros para comparação
- 🔄 **Atualização Manual**: Botão para limpar cache e recarregar dados

## 🚀 Como Executar

### Opção 1: Usando Docker Compose (Recomendado)

O dashboard é automaticamente iniciado com o pipeline completo:

```bash
# A partir da raiz do projeto
docker compose up -d

# Ou apenas o serviço streamlit
docker compose up -d streamlit
```

Acesse: http://localhost:8501

### Opção 2: Desenvolvimento Local

Para desenvolver ou testar localmente:

```bash
# Navegar para o diretório
cd streamlit_app

# Criar ambiente virtual (opcional)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export NYC_POSTGRES_HOST=localhost
export NYC_POSTGRES_PORT=5433
export NYC_POSTGRES_USER=nyc_user
export NYC_POSTGRES_PASSWORD=nyc_pass_123
export NYC_POSTGRES_DB=nyc_taxi_db

# Executar
streamlit run app.py
```

O dashboard estará disponível em: http://localhost:8501

## 🛠️ Tecnologias

- **Streamlit 1.31.0**: Framework para criação de dashboards interativos
- **Plotly 5.18.0**: Biblioteca para gráficos interativos
- **Pandas 2.2.0**: Manipulação e análise de dados
- **psycopg2-binary 2.9.9**: Driver PostgreSQL para Python

## 📊 Estrutura do Código

```python
streamlit_app/
├── app.py              # Aplicação principal do dashboard
├── Dockerfile          # Container Docker
├── requirements.txt    # Dependências Python
└── README.md          # Este arquivo
```

### Principais Componentes

#### Conexão com Banco de Dados
```python
@st.cache_resource
def get_connection():
    # Conexão persistente e cacheada
    return psycopg2.connect(...)
```

#### Cache de Queries
```python
@st.cache_data(ttl=300)  # Cache por 5 minutos
def run_query(query):
    # Queries são cacheadas para melhor performance
    return pd.read_sql_query(query, conn)
```

## 🔧 Configuração

### Variáveis de Ambiente

O dashboard usa as seguintes variáveis de ambiente:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `NYC_POSTGRES_HOST` | `localhost` | Host do PostgreSQL |
| `NYC_POSTGRES_PORT` | `5433` | Porta do PostgreSQL |
| `NYC_POSTGRES_USER` | `nyc_user` | Usuário do banco |
| `NYC_POSTGRES_PASSWORD` | `nyc_pass_123` | Senha do banco |
| `NYC_POSTGRES_DB` | `nyc_taxi_db` | Nome do banco de dados |

### Configuração do Streamlit

O dashboard está configurado com:
- **Layout**: Wide (usa toda a largura da tela)
- **Tema**: Light (pode ser alterado nas configurações do Streamlit)
- **Cache TTL**: 5 minutos para queries
- **Sidebar**: Expandida por padrão

## 📈 Usando o Dashboard

### 1. Acesse o Dashboard
Abra http://localhost:8501 no navegador

### 2. Configure os Filtros (Sidebar)
- Selecione o período de análise (datas)
- Escolha os bairros de interesse
- Clique em "Atualizar Dados" se necessário

### 3. Explore as Visualizações
- Role a página para ver diferentes análises
- Passe o mouse sobre os gráficos para ver detalhes
- Use os controles interativos do Plotly (zoom, pan, etc.)

### 4. Analise os Dados
- Compare métricas entre diferentes períodos
- Identifique padrões e tendências
- Explore rotas e bairros mais movimentados

## 🐛 Troubleshooting

### Dashboard não carrega

```bash
# Verificar se o container está rodando
docker compose ps streamlit

# Ver logs
docker compose logs -f streamlit
```

### Erro de conexão com banco de dados

```bash
# Verificar se o PostgreSQL está acessível
docker exec -it postgres-nyc-taxi psql -U nyc_user -d nyc_taxi_db -c "SELECT 1;"

# Verificar variáveis de ambiente
docker exec streamlit env | grep NYC_POSTGRES
```

### Dashboard mostra "Nenhum dado disponível"

Certifique-se de que:
1. A DAG do Airflow foi executada com sucesso
2. Existem dados na tabela `nyc_trips_silver`
3. Os filtros de data incluem o período com dados

```sql
-- Verificar dados disponíveis
SELECT
    MIN(tpep_pickup_datetime) as primeira_viagem,
    MAX(tpep_pickup_datetime) as ultima_viagem,
    COUNT(*) as total_viagens
FROM nyc_trips_silver;
```

### Performance lenta

1. **Limpar cache**: Use o botão "🔄 Atualizar Dados"
2. **Reduzir período**: Selecione um intervalo de datas menor
3. **Verificar recursos**: `docker stats streamlit`

## 🎨 Customização

### Alterar Tema

Crie `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#F63366"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

### Adicionar Novas Visualizações

1. Edite [app.py](app.py)
2. Crie nova query SQL
3. Use componentes do Streamlit e Plotly
4. Teste localmente
5. Rebuild do container: `docker compose up -d --build streamlit`

## 📚 Referências

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Python Documentation](https://plotly.com/python/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

---

Para mais informações sobre o pipeline completo, consulte o [README principal](../README.md).
