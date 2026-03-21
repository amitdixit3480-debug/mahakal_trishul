import streamlit as st
import sqlite3
import pandas as pd
import glob

# 1. पेज को चौड़ा (Wide) करना ताकि मैट्रिक्स अच्छी दिखे
st.set_page_config(page_title="Mahakal Seasonal Matrix", layout="wide")

# 2. डेटा लोड करने का मास्टर फंक्शन
@st.cache_data
def load_data():
    all_chunks = []
    db_files = glob.glob("mahakal_part_*") # आपकी बिना .db वाली फाइलें
    for file in db_files:
        try:
            conn = sqlite3.connect(file)
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

# --- UI: वही तारीखें जो आपको चाहिए थीं ---
c1, c2, c3, c4 = st.columns(4)
with c1: start_d = st.number_input("Start Day", 1, 31, 21)
with c2: start_m = st.number_input("Start Month", 1, 12, 3)
with c3: end_d = st.number_input("End Day", 1, 31, 21)
with c4: end_m = st.number_input("End Month", 1, 12, 4)

if st.button("🔱 महाकाल चक्र स्कैन करें"):
    if df.empty:
        st.error("डेटा नहीं मिला! कृपया फाइलें चेक करें।")
    else:
        results = []
        symbols = df['symbol'].unique()
        
        with st.spinner("⏳ इतिहास खंगाला जा रहा है..."):
            for sym in symbols:
                s_df = df[df['symbol'] == sym].sort_values('date')
                years = sorted(s_df['date'].dt.year.unique())
                row = {'Stock': sym}
                pos, total = 0, 0
                
                for yr in years:
                    try:
                        d1 = pd.Timestamp(year=yr, month=start_m, day=start_d)
                        d2 = pd.Timestamp(year=yr, month=end_m, day=end_d)
                        period = s_df[(s_df['date'] >= d1) & (s_df['date'] <= d2)]
                        if not period.empty:
                            ret = ((period['close'].iloc[-1] - period['close'].iloc[0]) / period['close'].iloc[0]) * 100
                            row[str(yr)] = round(ret, 2)
                            if ret > 0: pos += 1
                            total += 1
                    except: continue
                
                if total > 0:
                    row['Accuracy %'] = round((pos / total) * 100, 2)
                    results.append(row)

        # मैट्रिक्स तैयार करना
        matrix_df = pd.DataFrame(results)
        years_cols = [c for c in matrix_df.columns if c.isdigit()]
        cols = ['Stock', 'Accuracy %'] + years_cols
        matrix_df = matrix_df[cols].sort_values('Accuracy %', ascending=False)

        # 🎨 स्टाइलिंग (Green/Red bars जैसा लुक)
        def color_bg(val):
            if isinstance(val, (int, float)) and val != 0:
                color = '#90EE90' if val > 0 else '#FFB6C1'
                return f'background-color: {color}'
            return ''

        st.dataframe(matrix_df.style.applymap(color_bg, subset=years_cols), use_container_width=True, height=600)
