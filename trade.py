import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd

# Streamlit page setup
st.set_page_config(page_title="Stock Movement Scanner", layout="centered")
st.title("📊 US Stock Volatility & Trend Scanner")

# --- Input field ---
tickers_input = st.text_input(
    "Enter stock symbols (comma separated):",
    "TSLA, CZR, PYPL"
)

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

def analyze_stock(ticker):
    try:
        # --- Download data safely ---
        data = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=False)

        if data.empty:
            return {
                "Ticker": ticker,
                "Avg Volume": "❌ N/A",
                "IV30/RV30": "❌ N/A",
                "TS Slope": "❌ N/A",
                "Summary": "No data available"
            }

        # --- Average Volume ---
        avg_volume = data["Volume"].mean()
        volume_pass = avg_volume > 2_000_000

        # --- Calculate RV30 & IV30 safely ---
        rv30 = data["Close"].pct_change().rolling(30).std() * np.sqrt(252)
        iv30 = rv30 * 0.8  # Mock IV (simulated since real IV not in yfinance)

        # Get latest valid values safely
        rv30_last = rv30.dropna().iloc[-1:].values[0] if not rv30.dropna().empty else np.nan
        iv30_last = iv30.dropna().iloc[-1:].values[0] if not iv30.dropna().empty else np.nan

        if not np.isnan(rv30_last) and rv30_last != 0:
            iv_rv_ratio = iv30_last / rv30_last
        else:
            iv_rv_ratio = np.nan

        iv_rv_pass = bool(iv_rv_ratio > 1) if not np.isnan(iv_rv_ratio) else False

        # --- Trend slope 0→45 days ---
        if len(data["Close"]) >= 45:
            recent_close = data["Close"].tail(45)
            x = np.arange(len(recent_close))
            slope = np.polyfit(x, recent_close, 1)[0]
            slope_pass = bool(slope > 0)
        else:
            slope_pass = False

        # --- Summary logic ---
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

# --- Run button ---
if st.button("Run Scanner"):
