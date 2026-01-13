import streamlit as st

st.set_page_config(
    page_title="Crypto EMA200 Dashboard",
    layout="wide"
)

st.title("Crypto EMA200 Weekly Dashboard")

st.markdown("Monitor price distance to EMA200 for top cryptoassets")

st.info("""
This dashboard monitors the distance between current price and EMA200 on weekly timeframe.
- Positive values: Price above EMA200 (potential uptrend)
- Negative values: Price below EMA200 (potential downtrend)
- Greater than 30%: Overbought
- Less than -30%: Oversold
""")

st.subheader("Dashboard Status")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Status", "Active")
with col2:
    st.metric("Data Source", "Binance + CoinGecko")
with col3:
    st.metric("Timeframe", "Weekly")

st.subheader("How It Works")
st.write("""
1. Fetch top 200 cryptocurrencies from CoinGecko
2. Get weekly candlestick data from Binance API
3. Calculate EMA200 on weekly closes
4. Compute distance: (Close - EMA200) / EMA200 * 100
5. Display results in interactive dashboard
""")

st.divider()

st.text("GitHub: https://github.com/chamaobird/crypto-ema200-dashboard")
st.text("Made with Streamlit and Python")
