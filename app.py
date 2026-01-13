
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Crypto EMA200 Dashboard",
    page_icon="🔕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .metric-card {
        background-color: #1f1f1f;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #00d4ff;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_crypto_data():
    """
    Carregar dados do Google Sheets public CSV export
    Substitua a URL pela sua sheet em formato CSV
    """
    sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/export?format=csv"
    try:
        df = pd.read_csv(sheet_url)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Titulo principal
st.title("🔕 Crypto EMA200 Weekly Dashboard")
st.markdown("Monitore a distancia do preco atual a EMA200 semanal para os top 100 criptos")

# Carregar dados
df = load_crypto_data()

if df.empty:
    st.warning("Nenhum dado disponivel. Configure o link do Google Sheets.")
    st.stop()

# KPIs
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total de Moedas",
        len(df),
        delta=None,
        help="Numero de criptoativos monitorados"
    )

with col2:
    valid_data = df[df['dist_pct'].notna()]
    st.metric(
        "Com EMA200",
        len(valid_data),
        delta=f"{len(valid_data)/len(df)*100:.0f}%"
    )

with col3:
    overbought = len(df[df['dist_pct'] > 30])
    st.metric(
        "Sobrecomprados (>30%)",
        overbought,
        delta_color="inverse"
    )

with col4:
    oversold = len(df[df['dist_pct'] < -30])
    st.metric(
        "Sobrevendidos (<-30%)",
        oversold,
        delta_color="normal"
    )

# Sidebar - Filtros
st.sidebar.header("📋 Filtros")

search = st.sidebar.text_input("Buscar por simbolo ou nome", "").upper()
if search:
    df = df[df['symbol'].str.contains(search, case=False) | df['name'].str.contains(search, case=False)]

# Filtro por distancia
dist_min, dist_max = st.sidebar.slider(
    "Intervalo de distancia (%)",
    float(df['dist_pct'].min() or -100),
    float(df['dist_pct'].max() or 100),
    (float(df['dist_pct'].min() or -50), float(df['dist_pct'].max() or 50))
)
df = df[(df['dist_pct'] >= dist_min) & (df['dist_pct'] <= dist_max)]

# Abas principais
tab1, tab2, tab3 = st.tabs(["📊 Tabela", "📋 Rankings", 📝 Info"])

with tab1:
    st.subheader("Dados de Moedas")
    
    # Opcionalmente ordenar
    sort_col = st.selectbox(
        "Ordenar por",
        options=df.columns,
        index=list(df.columns).index('dist_pct') if 'dist_pct' in df.columns else 0
    )
    df_sorted = df.sort_values(by=sort_col, ascending=False)
    
    # Exibir tabela
    st.dataframe(
        df_sorted[['symbol', 'name', 'current_price', 'ema_200', 'dist_pct']].style.format({
            'current_price': '${:.2f}',
            'ema_200': '${:.2f}',
            'dist_pct': '{:.2f}%'
        }),
        use_container_width=True,
        height=500
    )

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🕻 Sobrecomprados (Top)")
        top_overbought = df.nlargest(10, 'dist_pct')[['symbol', 'dist_pct']]
        fig = px.bar(top_overbought, x='dist_pct', y='symbol', orientation='h', color='dist_pct')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader(📉 Sobrevendidos (Bottom)")
        top_oversold = df.nsmallest(10, 'dist_pct')[['symbol', 'dist_pct']]
        fig = px.bar(top_oversold, x='dist_pct', y='symbol', orientation='h', color='dist_pct')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Sobre este Dashboard")
    st.markdown("""
    ## Crypto EMA200 Weekly Monitor
    
    Este dashboard monitora a distancia do preco atual à EMA200 (média móvel exponencial de 200 periodos) no timeframe semanal.
    
    ### Interpretação:
    - **Positivo (+)**: Preço acima da EMA200 (potencial tendência de alta)
    - **Negativo (-)**: Preço abaixo da EMA200 (potencial tendência de baixa)
    - **>30%**: Sobrecomprado
    - **<-30%**: Sobrevendido
    
    ### Fonte de dados:
    - Top coins: CoinGecko API
    - Candles semanais: Binance Public API
    - Atualizado: 1x por semana
    
    ### Tech Stack:
    - Backend: Python (Binance + CoinGecko)
    - Storage: Google Sheets
    - Frontend: Streamlit
    """)
    
    st.info(f"Ultimo update: Verifique o timestamp nos dados")
