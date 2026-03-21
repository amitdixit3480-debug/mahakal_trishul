
import streamlit as st
import sqlite3
import pandas as pd
import glob

st.set_page_config(page_title="Mahakal Seasonal Matrix", layout="wide")

@st.cache_data
def load_data():
    all_chunks = []
    db_files = glob.glob("mahakal_part_*")
    for file in db_files:
        conn = sqlite3.connect(file)
        df_p = pd.read_sql_query("SELECT symbol, date, close FROM stock_data", conn)
        conn.close()
        all_chunks.append(df_p)
    final_df = pd.concat(all_chunks, ignore_index=True)
    final_df['date'] = pd.to_datetime(final_df['date'])
    return final_df

df = load_data()

st.title("🔱 Mahakal Seasonal Matrix Scanner")

# --- UI सेक्शन ---
c1, c2, c3, c4 = st.columns(4)
with c1: start_d = st.number_input("शुरुआत दिन", 1, 31, 21)
with c2: start_m = st.number_input("शुरुआत महीना", 1, 12, 3)
with c3: end_d = st.number_input("अंत दिन", 1, 31, 21)
with c4: end_m = st.number_input("अंत महीना", 1, 12, 4)

if st.button("🔱 स्कैन चक्र शुरू करें"):
    symbols = df['symbol'].unique()
    matrix_data = []

    with st.spinner("⏳ पूरे इतिहास का विश्लेषण किया जा रहा है..."):
        for sym in symbols:
            sym_df = df[df['symbol'] == sym].sort_values('date')
            years = sorted(sym_df['date'].dt.year.unique())
            
            row = {'Stock Name': sym}
            pos_years = 0
            count_years = 0
            total_ret = 0

            for yr in years:
                try:
                    d1 = pd.Timestamp(year=yr, month=start_m, day=start_d)
                    d2 = pd.Timestamp(year=yr, month=end_m, day=end_d)
                    
                    period = sym_df[(sym_df['date'] >= d1) & (sym_df['date'] <= d2)]
                    
                    if not period.empty:
                        ret = ((period['close'].iloc[-1] - period['close'].iloc[0]) / period['close'].iloc[0]) * 100
                        row[str(yr)] = round(ret, 2)
                        total_ret += ret
                        if ret > 0: pos_years += 1
                        count_years += 1
                except: continue
            
            if count_years > 0:
                row['Accuracy %'] = round((pos_years / count_years) * 100, 2)
                row['Avg Return %'] = round(total_ret / count_years, 2)
                matrix_data.append(row)

    # टेबल तैयार करना
    final_matrix = pd.DataFrame(matrix_data)
    
    # कॉलम को सही क्रम में लगाना (Name, Accuracy, Avg, then Years)
    cols = ['Stock Name', 'Accuracy %', 'Avg Return %'] + [c for c in final_matrix.columns if c.isdigit()]
    final_matrix = final_matrix[cols].sort_values('Accuracy %', ascending=False)

    # 🎨 स्टाइलिंग (जैसा आपकी इमेज में है)
    def color_coding(val):
        if isinstance(val, (int, float)):
            color = 'lightgreen' if val > 0 else '#ff9999' # Reddish for loss
            return f'background-color: {color}'
        return ''

    st.subheader(f"📊 {start_d}/{start_m} से {end_d}/{end_m} का सीजनल डेटा")
    st.dataframe(
        final_matrix.style.applymap(color_coding, subset=[c for c in final_matrix.columns if c != 'Stock Name']),
        use_container_width=True,
        height=600
    )
