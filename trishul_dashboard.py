import streamlit as st
import sqlite3
import pandas as pd
import glob

st.set_page_config(page_title="Mahakal Matrix", layout="wide")

@st.cache_data
def load_data():
    all_chunks = []
    # आपकी बिना .db एक्सटेंशन वाली फाइलों के लिए
    files = glob.glob("mahakal_part_*")
    for f in files:
        try:
            conn = sqlite3.connect(f)
            df_p = pd.read_sql_query("SELECT symbol, date, close FROM stock_data", conn)
            conn.close()
            all_chunks.append(df_p)
        except: continue
    if not all_chunks: return pd.DataFrame()
    final_df = pd.concat(all_chunks, ignore_index=True)
    final_df['date'] = pd.to_datetime(final_df['date'])
    return final_df

df = load_data()

st.title("🔱 Mahakal Seasonal Matrix Scanner")

# डेटा लोड होने की पुष्टि
if not df.empty:
    st.sidebar.success(f"✅ {len(df['symbol'].unique())} स्टॉक्स लोड हुए")
else:
    st.error("❌ डेटा लोड नहीं हुआ। कृपया फाइल चेक करें।")

# UI
c1, c2, c3, c4 = st.columns(4)
with c1: start_d = st.number_input("Start Day", 1, 31, 21)
with c2: start_m = st.number_input("Start Month", 1, 12, 3)
with c3: end_d = st.number_input("End Day", 1, 31, 21)
with c4: end_m = st.number_input("End Month", 1, 12, 4)

if st.button("🔱 स्कैन शुरू करें"):
    results = []
    symbols = df['symbol'].unique()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, sym in enumerate(symbols):
        status_text.text(f"Scanning: {sym}")
        s_df = df[df['symbol'] == sym].sort_values('date')
        years = sorted(s_df['date'].dt.year.unique())
        
        row = {'Stock': sym}
        found_any = False
        
        for yr in years:
            try:
                d1 = pd.Timestamp(year=yr, month=start_m, day=start_d)
                d2 = pd.Timestamp(year=yr, month=end_m, day=end_d)
                period = s_df[(s_df['date'] >= d1) & (s_df['date'] <= d2)]
                
                if not period.empty:
                    ret = ((period['close'].iloc[-1] - period['close'].iloc[0]) / period['close'].iloc[0]) * 100
                    row[str(yr)] = round(ret, 2)
                    found_any = True
            except: continue
        
        if found_any:
            results.append(row)
        progress_bar.progress((i + 1) / len(symbols))

    if results:
        status_text.text("✅ स्कैन पूरा हुआ!")
        matrix_df = pd.DataFrame(results)
        # ईयर कॉलम्स को अरेंज करना
        year_cols = sorted([c for c in matrix_df.columns if c.isdigit()])
        matrix_df = matrix_df[['Stock'] + year_cols]
        
        # डायरेक्ट टेबल डिस्प्ले (ताकि रिस्पॉन्स दिखे)
        st.dataframe(matrix_df, use_container_width=True)
    else:
        st.warning("इस तारीख के बीच कोई डेटा नहीं मिला।")
