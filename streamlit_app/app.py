import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Configuração da página
st.set_page_config(
    page_title="NYC Taxi Dashboard",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para conectar ao banco de dados
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=os.getenv('NYC_POSTGRES_HOST', 'localhost'),
        port=os.getenv('NYC_POSTGRES_PORT', '5433'),
        user=os.getenv('NYC_POSTGRES_USER', 'nyc_user'),
        password=os.getenv('NYC_POSTGRES_PASSWORD', 'nyc_pass_123'),
        database=os.getenv('NYC_POSTGRES_DB', 'nyc_taxi_db')
    )

# Função para executar queries
@st.cache_data(ttl=300)  # Cache por 5 minutos
def run_query(query):
    conn = get_connection()
    df = pd.read_sql_query(query, conn)
    return df

# Título principal
st.title("🚕 NYC Taxi Data Pipeline Dashboard")
st.markdown("---")

# Sidebar com filtros
with st.sidebar:
    st.header("Filtros")

    # Verificar datas disponíveis
    date_query = """
    SELECT
        MIN(DATE(tpep_pickup_datetime)) as min_date,
        MAX(DATE(tpep_pickup_datetime)) as max_date
    FROM public.nyc_trips_silver
    """
    date_range = run_query(date_query)

    if not date_range.empty and date_range['min_date'].iloc[0]:
        min_date = pd.to_datetime(date_range['min_date'].iloc[0])
        max_date = pd.to_datetime(date_range['max_date'].iloc[0])

        start_date = st.date_input(
            "Data Inicial",
            value=max_date - timedelta(days=7),
            min_value=min_date,
            max_value=max_date
        )

        end_date = st.date_input(
            "Data Final",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    else:
        st.warning("Nenhum dado disponível no banco")
        start_date = datetime.now().date()
        end_date = datetime.now().date()

    # Filtro de borough
    borough_query = """
    SELECT DISTINCT pickup_borough
    FROM public.nyc_trips_silver
    WHERE pickup_borough IS NOT NULL
    ORDER BY pickup_borough
    """
    boroughs_df = run_query(borough_query)

    selected_boroughs = st.multiselect(
        "Bairros (Pickup)",
        options=boroughs_df['pickup_borough'].tolist() if not boroughs_df.empty else [],
        default=boroughs_df['pickup_borough'].tolist() if not boroughs_df.empty else []
    )

    st.markdown("---")
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

# Construir filtro WHERE baseado nas seleções
where_conditions = [f"DATE(tpep_pickup_datetime) BETWEEN '{start_date}' AND '{end_date}'"]
if selected_boroughs:
    boroughs_str = "','".join(selected_boroughs)
    where_conditions.append(f"pickup_borough IN ('{boroughs_str}')")

where_clause = " AND ".join(where_conditions)

# KPIs principais
st.header("📊 Métricas Principais")

metrics_query = f"""
SELECT
    COUNT(*) as total_trips,
    ROUND(SUM(trip_distance)::numeric, 2) as total_distance,
    ROUND(AVG(trip_distance)::numeric, 2) as avg_distance,
    ROUND(SUM(total_amount)::numeric, 2) as total_revenue,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare,
    ROUND(AVG(EXTRACT(EPOCH FROM (tpep_dropoff_datetime - tpep_pickup_datetime))/60)::numeric, 2) as avg_duration_min
FROM public.nyc_trips_silver
WHERE {where_clause}
"""

metrics = run_query(metrics_query)

if not metrics.empty:
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Total de Viagens", f"{metrics['total_trips'].iloc[0]:,}")

    with col2:
        st.metric("Distância Total (mi)", f"{metrics['total_distance'].iloc[0]:,}")

    with col3:
        st.metric("Dist. Média (mi)", f"{metrics['avg_distance'].iloc[0]}")

    with col4:
        st.metric("Receita Total", f"${metrics['total_revenue'].iloc[0]:,.2f}")

    with col5:
        st.metric("Tarifa Média", f"${metrics['avg_fare'].iloc[0]:.2f}")

    with col6:
        st.metric("Duração Média (min)", f"{metrics['avg_duration_min'].iloc[0]}")

st.markdown("---")

# Gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Viagens por Dia")
    daily_query = f"""
    SELECT
        DATE(tpep_pickup_datetime) as date,
        COUNT(*) as trips
    FROM public.nyc_trips_silver
    WHERE {where_clause}
    GROUP BY DATE(tpep_pickup_datetime)
    ORDER BY date
    """
    daily_data = run_query(daily_query)

    if not daily_data.empty:
        fig = px.line(daily_data, x='date', y='trips',
                     title='Viagens ao Longo do Tempo',
                     labels={'date': 'Data', 'trips': 'Número de Viagens'})
        fig.update_traces(line_color='#1f77b4')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados para o período selecionado")

with col2:
    st.subheader("🏙️ Top 10 Bairros (Pickup)")
    borough_query = f"""
    SELECT
        pickup_borough,
        COUNT(*) as trips,
        ROUND(AVG(total_amount)::numeric, 2) as avg_revenue
    FROM public.nyc_trips_silver
    WHERE {where_clause} AND pickup_borough IS NOT NULL
    GROUP BY pickup_borough
    ORDER BY trips DESC
    LIMIT 10
    """
    borough_data = run_query(borough_query)

    if not borough_data.empty:
        fig = px.bar(borough_data, x='pickup_borough', y='trips',
                    title='Viagens por Bairro',
                    labels={'pickup_borough': 'Bairro', 'trips': 'Número de Viagens'},
                    color='avg_revenue',
                    color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados para o período selecionado")

# Segunda linha de gráficos
col3, col4 = st.columns(2)

with col3:
    st.subheader("⏰ Padrão de Demanda por Hora")
    hourly_query = f"""
    SELECT
        EXTRACT(HOUR FROM tpep_pickup_datetime) as hour,
        COUNT(*) as trips
    FROM public.nyc_trips_silver
    WHERE {where_clause}
    GROUP BY EXTRACT(HOUR FROM tpep_pickup_datetime)
    ORDER BY hour
    """
    hourly_data = run_query(hourly_query)

    if not hourly_data.empty:
        fig = px.bar(hourly_data, x='hour', y='trips',
                    title='Distribuição de Viagens por Hora do Dia',
                    labels={'hour': 'Hora do Dia', 'trips': 'Número de Viagens'})
        fig.update_traces(marker_color='#ff7f0e')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados para o período selecionado")

with col4:
    st.subheader("💳 Métodos de Pagamento")
    payment_query = f"""
    SELECT
        CASE
            WHEN payment_type = 1 THEN 'Cartão de Crédito'
            WHEN payment_type = 2 THEN 'Dinheiro'
            WHEN payment_type = 3 THEN 'Sem Cobrança'
            WHEN payment_type = 4 THEN 'Disputa'
            ELSE 'Outro'
        END as payment_method,
        COUNT(*) as trips
    FROM public.nyc_trips_silver
    WHERE {where_clause}
    GROUP BY payment_type
    ORDER BY trips DESC
    """
    payment_data = run_query(payment_query)

    if not payment_data.empty:
        fig = px.pie(payment_data, values='trips', names='payment_method',
                    title='Distribuição de Métodos de Pagamento')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados para o período selecionado")

# Tabela de rotas mais populares
st.markdown("---")
st.subheader("🗺️ Top 10 Rotas Mais Populares")

routes_query = f"""
SELECT
    pickup_borough,
    dropoff_borough,
    pickup_zone,
    dropoff_zone,
    COUNT(*) as trips,
    ROUND(AVG(trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare,
    ROUND(AVG(EXTRACT(EPOCH FROM (tpep_dropoff_datetime - tpep_pickup_datetime))/60)::numeric, 2) as avg_duration_min
FROM public.nyc_trips_silver
WHERE {where_clause}
    AND pickup_borough IS NOT NULL
    AND dropoff_borough IS NOT NULL
GROUP BY pickup_borough, dropoff_borough, pickup_zone, dropoff_zone
ORDER BY trips DESC
LIMIT 10
"""

routes_data = run_query(routes_query)

if not routes_data.empty:
    st.dataframe(
        routes_data,
        use_container_width=True,
        column_config={
            "pickup_borough": "Bairro Origem",
            "dropoff_borough": "Bairro Destino",
            "pickup_zone": "Zona Origem",
            "dropoff_zone": "Zona Destino",
            "trips": st.column_config.NumberColumn("Viagens", format="%d"),
            "avg_distance": st.column_config.NumberColumn("Dist. Média (mi)", format="%.2f"),
            "avg_fare": st.column_config.NumberColumn("Tarifa Média", format="$%.2f"),
            "avg_duration_min": st.column_config.NumberColumn("Duração Média (min)", format="%.1f")
        }
    )
else:
    st.info("Sem dados de rotas para o período selecionado")

# Análise de receita
st.markdown("---")
st.subheader("💰 Análise de Receita")

revenue_query = f"""
SELECT
    DATE(tpep_pickup_datetime) as date,
    SUM(total_amount) as daily_revenue,
    SUM(tip_amount) as daily_tips,
    AVG(total_amount) as avg_fare
FROM public.nyc_trips_silver
WHERE {where_clause}
GROUP BY DATE(tpep_pickup_datetime)
ORDER BY date
"""

revenue_data = run_query(revenue_query)

if not revenue_data.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=revenue_data['date'], y=revenue_data['daily_revenue'],
                            mode='lines', name='Receita Total',
                            line=dict(color='green', width=2)))
    fig.add_trace(go.Scatter(x=revenue_data['date'], y=revenue_data['daily_tips'],
                            mode='lines', name='Gorjetas',
                            line=dict(color='orange', width=2)))

    fig.update_layout(
        title='Receita e Gorjetas Diárias',
        xaxis_title='Data',
        yaxis_title='Valor ($)',
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Sem dados de receita para o período selecionado")

# Footer
st.markdown("---")
st.markdown("**NYC Taxi Data Pipeline Dashboard** | Atualizado em tempo real do PostgreSQL")
