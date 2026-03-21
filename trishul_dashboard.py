import streamlit as st
import sqlite3
import pandas as pd
import glob

st.set_page_config(page_title="Mahakal Matrix Scanner", layout="wide")

@st.cache_data
def load_data():
    all_chunks = []
    # आपकी फाइलों के नाम के हिसाब से (mahakal_part_1.db)
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
    final_df['date'] = pd.to_datetime(final_df['date'])
    return final_df

df = load_data()

st.title("🔱 Mahakal Seasonal Matrix Scanner")

if not df.empty:
    # UI Inputs
    c1, c2, c3, c4 = st.columns(4)
    with c1: start_d = st.number_input("Start Day", 1, 31, 21)
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
            valid_stock = False
            
            for yr in years:
                try:
                    # सटीक तारीख के बजाय उस महीने का डेटा ढूँढना (Better Logic)
                    d1 = pd.Timestamp(year=yr, month=start_m, day=start_d)
                    d2 = pd.Timestamp(year=yr, month=end_m, day=end_d)
                    
                    # अगर सटीक दिन न मिले तो अगले 3 दिन तक चेक करना
                    period = s_df[(s_df['date'] >= d1) & (s_df['date'] <= d2)]
                    
                    if not period.empty:
                        start_price = period['close'].iloc[0]
                        end_price = period['close'].iloc[-1]
                        ret = ((end_price - start_price) / start_price) * 100
                        row[str(yr)] = round(ret, 2)
                        valid_stock = True
                except: continue
            
            if valid_stock:
                results.append(row)

        if results:
            status.success("🔱 महाकाल ने चक्र ढूंढ लिया!")
            res_df = pd.DataFrame(results)
            year_cols = sorted([c for c in res_df.columns if c.isdigit()])
            res_df = res_df[['Stock Name'] + year_cols]
            
            # 🎨 Green/Red स्टाइलिंग (जैसा मोबाइल फोटो में था)
            def color_logic(v):
                if isinstance(v, (int, float)):
                    return f'background-color: {"#c6efce" if v > 0 else "#ffc7ce"}'
                return ''
            
            st.dataframe(res_df.style.applymap(color_logic, subset=year_cols), use_container_width=True)
        else:
            status.error("❌ कोई डेटा नहीं मिला। कृपया तारीखें बदलें।")
