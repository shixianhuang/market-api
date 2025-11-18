# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import datetime as dt

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="📈 Stock Market Dashboard", page_icon="💹", layout="wide")

st.title("📈 Stock Market Dashboard")
st.caption("Built with Streamlit + Yahoo Finance API (via yfinance).")

# -------------------------------
# Sidebar Controls
# -------------------------------
st.sidebar.header("🔍 Search Stock")
ticker = st.sidebar.text_input("Enter stock symbol (e.g., AAPL, TSLA, NVDA, MSFT):", "AAPL")

st.sidebar.subheader("📅 Date Range")
start_date = st.sidebar.date_input("Start date", dt.date(2024, 1, 1))
end_date = st.sidebar.date_input("End date", dt.date.today())

interval = st.sidebar.selectbox("Data interval", ["1d", "1wk", "1mo"], index=0)

show_info = st.sidebar.checkbox("Show Company Info", value=True)
show_stats = st.sidebar.checkbox("Show Key Statistics", value=True)
show_chart = st.sidebar.checkbox("Show Price Chart", value=True)
show_table = st.sidebar.checkbox("Show Data Table", value=True)

# -------------------------------
# Fetch Data
# -------------------------------
try:
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date, interval=interval)
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

# -------------------------------
# Display Information
# -------------------------------
st.subheader(f"💡 Stock Overview: {ticker}")

if show_info:
    info = stock.info
    st.write("**Company Name:**", info.get("longName", "N/A"))
    st.write("**Sector:**", info.get("sector", "N/A"))
    st.write("**Industry:**", info.get("industry", "N/A"))
    st.write("**Market Cap:**", f"{info.get('marketCap', 0):,}")
    st.write("**Website:**", info.get("website", "N/A"))

if show_stats:
    st.subheader("📊 Key Statistics")
    st.metric("Previous Close", f"{info.get('previousClose', 0):,.2f}")
    st.metric("52-Week High", f"{info.get('fiftyTwoWeekHigh', 0):,.2f}")
    st.metric("52-Week Low", f"{info.get('fiftyTwoWeekLow', 0):,.2f}")
    st.metric("Forward PE", info.get("forwardPE", "N/A"))
    st.metric("Dividend Yield", info.get("dividendYield", "N/A"))

if show_chart:
    st.subheader("📈 Price Chart")
    st.line_chart(df["Close"], use_container_width=True)

if show_table:
    st.subheader("📋 Historical Data")
    st.dataframe(df.tail(10))

# -------------------------------
# Footer
# -------------------------------
st.divider()
st.caption("Data provided by Yahoo Finance | App built with Streamlit")
