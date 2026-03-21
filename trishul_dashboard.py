
import streamlit as st
import sqlite3
import pandas as pd
import glob

st.set_page_config(page_title="Mahakal Matrix", layout="wide")

@st.cache_data
def load_data():
    all_chunks = []
    # आपकी फाइलों के नाम (mahakal_part_1.db) को सही से पढ़ना
    db_files = glob.glob("mahakal_part_*.db")
    for f in db_files:
        try:
            conn = sqlite3.connect(f)
            df_p = pd.read_sql_query("SELECT symbol, date, close FROM stock_data", conn)
            conn.close()
            all_chunks.append(df_p)
        except: continue
    if not all_chunks: return pd.DataFrame()
    final_df = pd.concat(all_chunks, ignore_index=True)
    # तारीखों को सही फॉर्मेट में बदलना
    final_df['date'] = pd.to_datetime(final_df['date'], errors='coerce')
    return final_df.dropna(subset=['date'])

df = load_data()

st.title("🔱 Mahakal Seasonal Matrix Scanner")

if not df.empty:
    c1, c2, c3, c4 = st.columns(4)
    with c1: start_d = st.number_input("Start Day", 1, 31, 13)
    with c2: start_m = st.number_input("Start Month", 1, 12, 3)
    with c3: end_d = st.number_input("End Day", 1, 31, 21)
    with c4: end_m = st.number_input("End Month", 1, 12, 4)

    if st.button("🔱 महाकाल चक्र स्कैन शुरू करें"):
        results = []
        symbols = df['symbol'].unique()
        status = st.empty()
        
        for sym in symbols:
            status.text(f"🔍 विश्लेषण: {sym}")
            s_df = df[df['symbol'] == sym].sort_values('date')
            years = sorted(s_df['date'].dt.year.unique())
            row = {'Stock Name': sym}
            valid = False
            
            for yr in years:
                try:
                    # तारीखों को रेंज में ढूंढना ताकि छुट्टी होने पर भी डेटा मिल जाए
                    d1 = pd.Timestamp(year=yr, month=start_m, day=start_d)
                    d2 = pd.Timestamp(year=yr, month=end_m, day=end_d)
                    
                    period = s_df[(s_df['date'] >= d1) & (s_df['date'] <= d2)]
                    if not period.empty:
                        ret = ((period['close'].iloc[-1] - period['close'].iloc[0]) / period['close'].iloc[0]) * 100
                        row[str(yr)] = round(ret, 2)
                        valid = True
                except: continue
            
            if valid: results.append(row)

        if results:
            status.success("🔱 महाकाल ने चक्र पूर्ण किया!")
            res_df = pd.DataFrame(results)
            year_cols = sorted([c for c in res_df.columns if c.isdigit()])
            
            # स्टाइलिंग (Green/Red)
            def color_map(val):
                if isinstance(val, (int, float)):
                    return f'background-color: {"#c6efce" if val > 0 else "#ffc7ce"}'
                return ''
            
            st.dataframe(res_df.style.applymap(color_map, subset=year_cols), use_container_width=True)
        else:
            status.error("❌ कोई डेटा नहीं मिला। कृपया GitHub पर फाइलें चेक करें।")
