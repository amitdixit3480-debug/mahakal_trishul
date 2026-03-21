import streamlit as st
import sqlite3
import pandas as pd
import glob
import os
# 1. पेज सेटअप (Wide Layout)
st.set_page_config(page_title="Mahakal Time Cycle", layout="wide")

# 2. मल्टी-पार्ट डेटा लोड करने वाला फंक्शन
@st.cache_data
def load_combined_data():
    all_chunks = []
    # आपके फोल्डर में जितनी भी 'mahakal_part_*.db' फाइलें हैं, सबको ढूंढना
    db_files = glob.glob("mahakal_part_*.db")
    
    if not db_files:
        st.error("❌ कोई डेटाबेस पार्ट (Part 1, 2...) नहीं मिला! कृपया GitHub पर फाइलें चेक करें।")
        return pd.DataFrame()

    with st.spinner(f"⏳ {len(db_files)} डेटा पार्ट्स को महाकाल चक्र में जोड़ा जा रहा है..."):
        for file in db_files:
            try:
                conn = sqlite3.connect(file)
                # सिर्फ जरूरी कॉलम उठाना ताकि ऐप सुपर फ़ास्ट चले
                df_part = pd.read_sql_query("SELECT symbol, date, close FROM stock_data", conn)
                conn.close()
                all_chunks.append(df_part)
            except Exception as e:
                st.warning(f"⚠️ {file} को पढ़ने में दिक्कत आई: {e}")
        
        # सभी पार्ट्स को एक साथ मिलाना
        final_df = pd.concat(all_chunks, ignore_index=True)
        final_df['date'] = pd.to_datetime(final_df['date'])
        return final_df

# --- मुख्य प्रोग्राम शुरू ---
try:
    df = load_combined_data()

    if not df.empty:
        st.title("🔱 Mahakal Time Cycle & Seasonal Scanner")
        st.sidebar.success(f"✅ कुल {df['symbol'].nunique()} स्टॉक्स का डेटा तैयार है।")

        # --- UI: स्टॉक सिलेक्शन और साइकिल सेटिंग ---
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            all_stocks = sorted(df['symbol'].unique())
            selected_stock = st.selectbox("🎯 स्टॉक चुनें (Search here)", all_stocks)
        
        with col2:
            cycle_days = st.number_input("⏳ टाइम साइकिल के दिन (उदा. 90, 180)", value=90, min_value=10)

        # --- टाइम साइकिल की गणना (Logic) ---
        stock_df = df[df['symbol'] == selected_stock].sort_values('date')
        
        st.divider()
        st.subheader(f"📊 {selected_stock} का मूल्य और समय चक्र विश्लेषण")
        
        # चार्ट दिखाना
        st.line_chart(stock_df.set_index('date')['close'])

        # टाइम साइकिल हिट्स (Gann Logic जैसी खोज)
        st.info(f"💡 {selected_stock} में हर {cycle_days} दिन बाद होने वाले बदलावों की जांच की जा रही है...")
        
        # यहाँ हम भविष्य में साइकिल एक्यूरेसी (Success Rate) जोड़ेंगे

except Exception as e:
    st.error(f"❌ ऐप में कोई त्रुटि आई: {e}")
