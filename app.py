import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Stock Data Screener", layout="wide")

# --- DATA FETCHING FUNCTION ---
def fetch_stock_data(tickers):
    data = []
    
    for symbol in tickers:
        symbol = symbol.strip().upper()
        if not symbol:
            continue
            
        try:
            ticker = yf.Ticker(symbol)
            # Fetch 1 year of history
            hist = ticker.history(period="1y")
            info = ticker.info
            
            # Check if data is empty (invalid symbol)
            if hist.empty:
                st.error(f"⚠️ No data found for symbol: '{symbol}'")
                continue
                
            # Current Price
            current_price = hist['Close'].iloc[-1]
            
            # Market Cap (Handle missing keys safely)
            market_cap = info.get('marketCap', 'N/A')
            
            # 52-Week Metrics
            low_52w = hist['Low'].min()
            high_52w = hist['High'].max()
            
            pct_from_52w_low = ((current_price - low_52w) / low_52w) * 100
            pct_from_52w_high = ((current_price - high_52w) / high_52w) * 100
            
            # Bollinger Bands (20-day)
            sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            std_20 = hist['Close'].rolling(window=20).std().iloc[-1]
            
            bb_low = sma_20 - (2 * std_20)
            bb_high = sma_20 + (2 * std_20)
            
            pct_from_bb_low = ((current_price - bb_low) / bb_low) * 100
            pct_from_bb_high = ((current_price - bb_high) / bb_high) * 100
            
            # Append to list with NEW SHORT NAMES
            data.append({
                "Symbol": symbol,
                "Current": current_price,
                "MCap": market_cap,
                "52L": low_52w,
                "52H": high_52w,
                "%52L": pct_from_52w_low,
                "%52H": pct_from_52w_high,
                "%BBL": pct_from_bb_low,
                "%BBH": pct_from_bb_high
            })
            
        except Exception as e:
            st.error(f"❌ Error fetching '{symbol}': {e}")
            
    return pd.DataFrame(data)

# --- SESSION STATE SETUP ---
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
if "last_updated" not in st.session_state:
    st.session_state.last_updated = "Never"

# --- MAIN APP UI ---
st.title("📈 Stock Data Screener")

# Input for symbols
default_symbols = "AVGO,GOOG,TSM,MRVL,CRDO,SOXL,TQQQ,TSLA,MU,AMZN,MSFT"
ticker_input = st.text_input("Enter Stock Symbols (comma-separated):", default_symbols)

# Wrapper function to update state
def update_data():
    ticker_list = ticker_input.split(",")
    new_df = fetch_stock_data(ticker_list)
    
    # Only update state if we got data back
    if not new_df.empty:
        st.session_state.df = new_df
        st.session_state.last_updated = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

# --- AUTO-UPDATE LOGIC ---
if st.session_state.df.empty:
    with st.spinner("Fetching morning data..."):
        update_data()

# --- CONTROL BAR (Timestamp & Refresh) ---
col1, col2 = st.columns([3, 1])

with col1:
    st.info(f"🕒 **Last Updated:** {st.session_state.last_updated}")

with col2:
    if st.button("🔄 Refresh Now", use_container_width=True):
        with st.spinner("Pulling latest data..."):
            update_data()
            st.rerun() 

# --- DISPLAY LOGIC ---
if not st.session_state.df.empty:
    df_display = st.session_state.df.copy()
    
    # 1. Format Market Cap nicely (Trillions/Billions/Millions)
    def format_market_cap(x):
        if isinstance(x, (int, float)):
            if x >= 1e12: return f"${x/1e12:.2f}T"
            elif x >= 1e9: return f"${x/1e9:.2f}B"
            elif x >= 1e6: return f"${x/1e6:.2f}M"
        return x
    
    # Check for new column name "MCap"
    if 'MCap' in df_display.columns:
        df_display['MCap'] = df_display['MCap'].apply(format_market_cap)

    # 2. Define Styling Logic
    def color_percentages(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return 'color: #2e8b57; font-weight: bold;' # Green
            elif val < 0:
                return 'color: #ff4b4b; font-weight: bold;' # Red
        return ''

    # Identify columns for specific formatting using NEW NAMES
    pct_cols = [c for c in ["%52L", "%52H", "%BBL", "%BBH"] if c in df_display.columns]
    price_cols = [c for c in ["Current", "52L", "52H"] if c in df_display.columns]

    # 3. Apply Pandas Styler
    styled_df = df_display.style
    
    # Center all text in cells
    styled_df = styled_df.set_properties(**{'text-align': 'center'})
    
    # Center all headers
    styled_df = styled_df.set_table_styles([dict(selector='th', props=[('text-align', 'center')])])

    # Apply Green/Red colors to percentage columns and add '%' sign
    if pct_cols:
        styled_df = styled_df.map(color_percentages, subset=pct_cols)
        styled_df = styled_df.format("{:.2f}%", subset=pct_cols)

    # Force 2 decimal places for price columns
    if price_cols:
        styled_df = styled_df.format("{:.2f}", subset=price_cols)

    # 4. Render the table

    st.dataframe(styled_df, use_container_width=True, hide_index=True)
