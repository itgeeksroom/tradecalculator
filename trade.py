import yfinance as yf
import numpy as np
import pandas as pd

def analyze_stock(ticker):
    data = yf.download(ticker, period="6mo", interval="1d", progress=False)
    if data.empty:
        return {"Ticker": ticker, "Result": "No data"}

    # --- Average Volume ---
    avg_volume = data['Volume'].mean()
    volume_pass = avg_volume > 2_000_000  # Adjust threshold as you wish

    # --- IV30 / RV30 approximation ---
    rv30 = data['Close'].pct_change().rolling(30).std() * np.sqrt(252)
    iv30 = rv30 * 0.8  # mock IV (since yfinance doesn't provide IV)
    iv_rv_ratio = iv30.iloc[-1] / rv30.iloc[-1] if rv30.iloc[-1] != 0 else 0
    iv_rv_pass = iv_rv_ratio > 1

    # --- Trend Slope 0→45 days ---
    recent_close = data['Close'].tail(45)
    x = np.arange(len(recent_close))
    slope = np.polyfit(x, recent_close, 1)[0]
    slope_pass = slope > 0

    # --- Summary logic ---
    if not iv_rv_pass:
        summary = f"{ticker} may not move much"
    elif slope_pass and volume_pass:
        summary = f"{ticker} showing bullish setup"
    else:
        summary = f"{ticker} trend unclear"

    return {
        "Ticker": ticker,
        "Avg Volume": "PASS" if volume_pass else "FAIL",
        "IV30 / RV30": "PASS" if iv_rv_pass else "FAIL",
        "TS Slope 0→45": "PASS" if slope_pass else "FAIL",
        "Summary": summary
    }

# --- Run analysis ---
tickers = ["CZR", "PYPL"]
results = [analyze_stock(t) for t in tickers]
df = pd.DataFrame(results)
print(df)
