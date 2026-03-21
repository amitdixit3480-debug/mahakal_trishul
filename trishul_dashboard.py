import streamlit as st
import sqlite3
import pandas as pd
import glob

st.set_page_config(page_title="Mahakal Seasonal Scanner", layout="wide")

@st.cache_data
def load_data():
    all_chunks = []
    db_files = glob.glob("mahakal_part_*")
    for file in db_files:
        conn = sqlite3.connect(file)
        # डेटा लोड करते समय ही डेट को सही फॉर्मेट में लाना
        df_part = pd.read_sql_query("SELECT symbol, date, close FROM stock_data", conn)
        conn.close()
        all_chunks.append(df_part)
    final_df = pd.concat(all_chunks, ignore_index=True)
    final_df['date'] = pd.to_datetime(final_df['date'])
    return final_df

df = load_data()

st.title("🔱 Mahakal Seasonal Matrix Scanner")

# --- UI: तारीख का चुनाव (जैसा आपकी इमेज में है) ---
col1, col2, col3 = st.columns(3)
with col1:
    start_day = st.number_input("शुरुआत दिन", min_value=1, max_value=31, value=21)
    start_month = st.number_input("शुरुआत महीना", min_value=1, max_value=12, value=3)
with col2:
    end_day = st.number_input("अंत दिन", min_value=1, max_value=31, value=21)
    end_month = st.number_input("अंत महीना", min_value=1, max_value=12, value=4)

if st.button("🔱 स्कैन चक्र शुरू करें"):
    symbols = df['symbol'].unique()
    seasonal_results = []

    for sym in symbols:
        sym_df = df[df['symbol'] == sym].sort_values('date')
        years = sym_df['date'].dt.year.unique()
        
        row = {'Name': sym}
        total_positive = 0
        total_years = 0

        for year in years:
            # हर साल के लिए उस तारीख की रेंज का डेटा निकालना
            try:
                d1 = pd.Timestamp(year=year, month=start_month, day=start_day)
                d2 = pd.Timestamp(year=year, month=end_month, day=end_day)
                
                period = sym_df[(sym_df['date'] >= d1) & (sym_df['date'] <= d2)]
                
                if not period.empty:
                    ret = ((period['close'].iloc[-1] - period['close'].iloc[0]) / period['close'].iloc[0]) * 100
                    row[str(year)] = round(ret, 2)
                    if ret > 0: total_positive += 1
                    total_years += 1
            except: continue
        
        if total_years > 0:
            row['Accuracy %'] = round((total_positive / total_years) * 100, 2)
            seasonal_results.append(row)

    # टेबल दिखाना
    result_df = pd.DataFrame(seasonal_results)
    # Accuracy के हिसाब से सॉर्ट करना ताकि बेस्ट स्टॉक्स ऊपर आएं
    result_df = result_df.sort_values('Accuracy %', ascending=False)
    
    st.dataframe(result_df.style.background_gradient(cmap='RdYlGn', axis=None))
