import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Crypto EMA200 Dashboard", layout="wide")

st.title("🔕 Crypto EMA200 Weekly Dashboard")
st.markdown("Monitore a distância do preço atual à EMA200 semanal para top criptos")

# Tentar carregar o arquivo CSV local
csv_files = ['crypto_ema200_top50.csv', 'crypto_ema200_test.csv', 'crypto_ema200_latest.csv']
df = None

for file in csv_files:
    if os.path.exists(file):
        df = pd.read_csv(file)
        st.success(f"✅ Dados carregados de: {file}")
        break

if df is None or df.empty:
    st.warning("⚠️ Nenhum arquivo CSV encontrado. Verifique se crypto_ema200_top50.csv existe.")
    st.info("Arquivos esperados: " + ", ".join(csv_files))
else:
    st.metric("Total de Moedas", len(df))
    
    st.subheader("📊 Dados de Criptoativos")
    st.dataframe(df, use_container_width=True)
    
    st.subheader("📋 Estatísticas")
    if 'dist_pct' in df.columns:
        st.write(f"Distância MAX: {df['dist_pct'].max():.2f}%")
        st.write(f"Distância MIN: {df['dist_pct'].min():.2f}%")
        st.write(f"Distância MÉDIA: {df['dist_pct'].mean():.2f}%")
