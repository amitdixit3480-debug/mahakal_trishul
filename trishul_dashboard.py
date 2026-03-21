
import streamlit as st
import sqlite3
import pandas as pd
import glob
from datetime import timedelta

st.set_page_config(page_title="Mahakal Seasonal Matrix", layout="wide")

@st.cache_data
def load_data():
    all_chunks = []
    # आपकी .db फाइलें ढूँढना
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
    # 1. इनपुट सेक्शन
    col1, col2 = st.columns(2)
    with col1: start_str = st.text_input("Start Date (DD-Mon)", "01-Apr")
    with col2: end_str = st.text_input("End Date (DD-Mon)", "31-May")

    if st.button("🚩 महाकाल चक्र स्कैन शुरू करें"):
        symbols = df['symbol'].unique()
        current_year = 2026 # आपकी इमेज के अनुसार
        years = [current_year - i for i in range(1, 11)] # पिछले 10 साल (2025 से 2016)
        
        table_data = []
        status = st.empty()
        bar = st.progress(0)

        for i, sym in enumerate(symbols):
            status.text(f"🔍 विश्लेषण: {sym}")
            s_df = df[df['symbol'] == sym].set_index('date').sort_index()
            
            row = {'Stock': sym}
            returns = []
            wins = 0
            valid_yrs = 0

            for yr in years:
                start_price, end_price = None, None
                # Apps Script वाला 'Find Nearest Price' (7 दिन का बफर)
                try:
                    t_start = pd.to_datetime(f"{start_str}-{yr}")
                    for d in range(8):
                        sd = t_start + timedelta(days=d)
                        if sd in s_df.index:
                            start_price = s_df.loc[sd, 'close']
                            if isinstance(start_price, pd.Series): start_price = start_price.iloc[0]
                            break
                    
                    t_end = pd.to_datetime(f"{end_str}-{yr}")
                    for d in range(8):
                        ed = t_end + timedelta(days=d)
                        if ed in s_df.index:
                            end_price = s_df.loc[ed, 'close']
                            if isinstance(end_price, pd.Series): end_price = end_price.iloc[0]
                            break
                except: pass

                if start_price and end_price:
                    ret = ((end_price - start_price) / start_price) * 100
                    row[str(yr)] = round(ret, 2)
                    returns.append(ret)
                    if ret > 0: wins += 1
                    valid_yrs += 1
                else:
                    row[str(yr)] = None

            # शीट वाला फिल्टर: कम से कम 3 साल का डेटा जरूरी
            if valid_yrs >= 3:
                avg_ret = sum(returns) / len(returns)
                win_rate = (wins / valid_yrs) * 100
                # आपका फार्मूला: (WinRate * 0.7) + (Avg * 0.3)
                score = (win_rate * 0.7) + (avg_ret * 0.3)
                
                row['Score'] = round(score, 2)
                row['Avg Return'] = f"{round(avg_ret, 2)}%"
                row['Win Rate'] = f"{wins}/{valid_yrs} ({round(win_rate, 0)}%)"
                table_data.append(row)
            
            bar.progress((i + 1) / len(symbols))

        if table_data:
            status.success("🚩 महाकाल की कृपा से रिपोर्ट तैयार है!")
            res_df = pd.DataFrame(table_data)
            
            # कॉलम अरेंजमेंट
            year_cols = [str(y) for y in years]
            final_cols = ['Stock', 'Score', 'Avg Return', 'Win Rate'] + year_cols
            res_df = res_df[final_cols].sort_values('Score', ascending=False)

            # 🎨 कलर फॉर्मेटिंग (Green for Profit, Red for Loss)
            def color_cells(val):
                if isinstance(val, (int, float)):
                    color = "#b7e1cd" if val > 0 else "#f4cccc"
                    return f'background-color: {color}'
                return ''

            st.dataframe(
                res_df.style.applymap(color_cells, subset=year_cols),
                use_container_width=True, height=700
            )
        else:
            status.error("❌ कोई डेटा नहीं मिला।")
