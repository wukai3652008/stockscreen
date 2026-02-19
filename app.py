import streamlit as st
import yfinance as yf
import pandas as pd

def fetch_stock_data(tickers):
    data = []
    
    for symbol in tickers:
        symbol = symbol.strip().upper()
        if not symbol:
            continue
            
        try:
            ticker = yf.Ticker(symbol)
            # Fetch 1 year of data to cover the 52-week high/low and 20-day calculations
            hist = ticker.history(period="1y")
            info = ticker.info
            
            if hist.empty:
                continue
                
            # Current Price
            current_price = hist['Close'].iloc[-1]
            
            # Market Cap
            market_cap = info.get('marketCap', 'N/A')
            
            # 52-Week Metrics
            low_52w = hist['Low'].min()
            high_52w = hist['High'].max()
            
            pct_from_52w_low = ((current_price - low_52w) / low_52w) * 100
            pct_from_52w_high = ((current_price - high_52w) / high_52w) * 100
            
            # 20-Day Bollinger Bands
            # 1. 20-day Simple Moving Average (SMA)
            sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            # 2. 20-day Standard Deviation
            std_20 = hist['Close'].rolling(window=20).std().iloc[-1]
            
            # 3. Calculate Upper and Lower Bands
            bb_low = sma_20 - (2 * std_20)
            bb_high = sma_20 + (2 * std_20)
            
            pct_from_bb_low = ((current_price - bb_low) / bb_low) * 100
            pct_from_bb_high = ((current_price - bb_high) / bb_high) * 100
            
            # Append row to our data list
            data.append({
                "Symbol": symbol,
                "Current Price": round(current_price, 2),
                "Market Cap": market_cap,
                "52-Week Low": round(low_52w, 2),
                "52-Week High": round(high_52w, 2),
                "% From 52W Low": round(pct_from_52w_low, 2),
                "% From 52W High": round(pct_from_52w_high, 2),
                "% From 20D BB Low": round(pct_from_bb_low, 2),
                "% From 20D BB High": round(pct_from_bb_high, 2)
            })
            
        except Exception as e:
            st.error(f"Failed to fetch data for {symbol}: {e}")
            
    return pd.DataFrame(data)

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Stock Data Screener", layout="wide")
st.title("📈 Stock Data Screener")

# Input field for stock symbols
default_symbols = "AAPL, MSFT, TSLA, NVDA"
ticker_input = st.text_input("Enter Stock Symbols (comma-separated):", default_symbols)

# The Refresh Button
if st.button("Refresh Data"):
    with st.spinner("Pulling latest data from Yahoo Finance..."):
        # Process the input string into a list
        ticker_list = ticker_input.split(",")
        
        # Fetch data and generate DataFrame
        df = fetch_stock_data(ticker_list)
        
        if not df.empty:
            # Format Market Cap to make it more readable (optional but recommended)
            # We convert large numbers to Billions (B) or Trillions (T)
            def format_market_cap(x):
                if isinstance(x, (int, float)):
                    if x >= 1e12:
                        return f"${x/1e12:.2f}T"
                    elif x >= 1e9:
                        return f"${x/1e9:.2f}B"
                    elif x >= 1e6:
                        return f"${x/1e6:.2f}M"
                return x
                
            df['Market Cap'] = df['Market Cap'].apply(format_market_cap)
            
            # Display the DataFrame as an interactive table
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("No valid data found. Please check your ticker symbols.")