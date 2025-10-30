import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd

# Streamlit page setup
st.set_page_config(page_title="Stock Movement Scanner", layout="centered")
st.title("📊 US Stock Volatility & Trend Scanner")

# Input field for stock symbols
tickers_input = st.text_input(
    "Enter stock symbols (comma separated):",
    "TSLA, CZR, PYPL"
)

# Split and clean input
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

def analyze_stock(ticker):
    try:
        # --- Fetch Data ---
        data = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=False)

        if data.empty:
            return {
                "Ticker": ticker,
                "Avg Volume": "❌ N/A",
                "IV30/RV30": "❌ N/A",
                "TS Slope": "❌ N/A",
                "Summary": "No data"
            }

        # --- Average Volume ---
        avg_volume = data["Volume"].mean()
        volume_pass = avg_volume > 2_000_000

        # --- IV30 / RV30 approximation ---
        rv30 = data["Close"].pct_change().rolling(30).std() * np.sqrt(252)
        iv30 = rv30 * 0.8  # Mock IV (since yfinance doesn't provide real IV)

        rv30_valid = rv30.dropna()
        iv30_valid = iv30.dropna()

        if not rv30_valid.empty:
            rv30_last = rv30_valid.iloc[-1]
            iv30_last = iv30_valid.iloc[-1]
        else:
            rv30_last = np.nan
            iv30_last = np.nan

        if pd.notna(rv30_last) and rv30_last != 0:
            iv_rv_ratio = iv30_last / rv30_last
        else:
            iv_rv_ratio = np.nan

        iv_rv_pass = iv_rv_ratio > 1 if not np.isnan(iv_rv_ratio) else False

        # --- Trend Slope 0→45 days ---
        if len(data["Close"]) >= 45:
            recent_close = data["Close"].tail(45)
            x = np.arange(len(recent_close))
            slope = np.polyfit(x, recent_close, 1)[0]
            slope_pass = slope > 0
        else:
            slope_pass = False

        # --- Summary Decision ---
        if not iv_rv_pass:
            summary = f"{ticker} may not move much"
        elif slope_pass and volume_pass:
            summary = f"{ticker} showing bullish setup"
        elif not slope_pass and volume_pass:
            summary = f"{ticker} showing bearish setup"
        else:
            summary = f"{ticker} trend unclear"

        # --- Helper to format pass/fail ---
        def pf(val):
            return "✅ PASS" if val else "❌ FAIL"

        return {
            "Ticker": ticker,
            "Avg Volume": pf(volume_pass),
            "IV30/RV30": pf(iv_rv_pass),
            "TS Slope": pf(slope_pass),
            "Summary": summary
        }

    except Exception as e:
        return {
            "Ticker": ticker,
            "Avg Volume": "❌ Error",
            "IV30/RV30": "❌ Error",
            "TS Slope": "❌ Error",
            "Summary": f"Error: {e}"
        }

# --- Run on Button Click ---
if st.button("Run Scanner"):
    with st.spinner("Fetching and analyzing data..."):
        results = [analyze_stock(t) for t in tickers]
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        st.success("✅ Scan complete!")

st.caption("Built with ❤️ using Streamlit & Yahoo Finance API")
