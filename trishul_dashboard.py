import streamlit as st
import sqlite3
import pandas as pd
import gdown
import os
import plotly.express as px

# पेज की सेटिंग
st.set_page_config(page_title="Scanner Mahakal", layout="wide")

# CSS: इमेज जैसा लुक देने के लिए (Custom Styling)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #ff4b4b; color: white; }
    .metric-card { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_value=True)

@st.cache_resource
def get_database():
    file_id = '1wZUXInDaLA153yYmjM3mdNLcpBbsuwUN'
    url = f'https://drive.google.com/uc?id={file_id}'
    output = 'mahakal_market_cloud.db'
    if not os.path.exists(output):
        with st.spinner("⏳ डेटाबेस लोड हो रहा है..."):
            gdown.download(url, output, quiet=False)
    return output

@st.cache_data
def load_data(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT date, close, symbol FROM stock_data", conn)
    conn.close()
    df['date'] = pd.to_datetime(df['date'])
    df['day_month'] = df['date'].dt.strftime('%d-%b')
    return df

try:
    db_path = get_database()
    df = load_data(db_path)

    # --- TOP HEADER (इमेज जैसा सिलेक्शन बॉक्स) ---
    with st.container():
        st.subheader("📊 Select date range")
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        
        start_day = c1.selectbox("Start Day", range(1, 32), index=0)
        start_month = c2.selectbox("Start Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], index=2)
        end_day = c3.selectbox("End Day", range(1, 32), index=20)
        end_month = c4.selectbox("End Month", ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], index=3)
        
        start_dm = f"{start_day:02d}-{start_month}"
        end_dm = f"{end_day:02d}-{end_month}"

    if st.button("🔱 Apply Scanner"):
        results = []
        symbols = df['symbol'].unique()
        
        for s in symbols:
            s_data = df[df['symbol'] == s]
            years = sorted(s_data['date'].dt.year.unique(), reverse=True)
            
            stock_record = {"Name": s}
            wins = 0
            valid_years = 0
            
            for yr in years[:8]: # पिछले 8 सालों का डेटा (इमेज की तरह)
                yr_df = s_data[s_data['date'].dt.year == yr]
                start_p = yr_df[yr_df['day_month'] >= start_dm].head(1)
                end_p = yr_df[yr_df['day_month'] <= end_dm].tail(1)

                if not start_p.empty and not end_p.empty:
                    ret = ((end_p['close'].values[0] - start_p['p_close'].values[0] if 'p_close' in end_p else end_p['close'].values[0] - start_p['close'].values[0]) / start_p['close'].values[0]) * 100
                    stock_record[f"{yr}"] = round(ret, 2)
                    if ret > 0: wins += 1
                    valid_years += 1
            
            if valid_years >= 3:
                stock_record["Accuracy"] = round((wins / valid_years) * 100, 0)
                results.append(stock_record)

        if results:
            final_df = pd.DataFrame(results)
            # कॉलम का आर्डर सही करना
            cols = ["Name", "Accuracy"] + [c for c in final_df.columns if c not in ["Name", "Accuracy"]]
            final_df = final_df[cols].sort_values("Accuracy", ascending=False)

            # --- डेटा डिस्प्ले (इमेज जैसा टेबल) ---
            # Pandas styling for Bar charts in columns
            def color_bar(val):
                color = '#2ecc71' if val > 0 else '#e74c3c'
                return f'background: linear-gradient(90deg, {color} {val}%, transparent {val}%);'

            st.write(f"### Found {len(final_df)} Stocks for this Period")
            st.dataframe(final_df.style.format(precision=2).background_gradient(subset=["Accuracy"], cmap="RdYlGn"))
        else:
            st.warning("No data found for the selected range.")

except Exception as e:
    st.error(f"Error: {e}")
