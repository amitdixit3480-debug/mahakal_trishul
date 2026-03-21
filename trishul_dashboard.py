import streamlit as st
import sqlite3
import pandas as pd
import os
import glob

# पेज सेटिंग
st.set_page_config(page_title="Scanner Mahakal Cycle", layout="wide")

@st.cache_data
def load_all_data():
    all_data = []
    # आपके फोल्डर में जितनी भी mahakal_part_...db फाइलें हैं, सबको ढूंढना
    db_files = glob.glob("mahakal_part_*.db")
    
    if not db_files:
        st.error("❌ कोई डेटाबेस पार्ट नहीं मिला! कृपया GitHub चेक करें।")
        return pd.DataFrame()

    with st.spinner(f"⏳ {len(db_files)} डेटा पार्ट्स को जोड़ा जा रहा है..."):
        for file in db_files:
            conn = sqlite3.connect(file)
            # सिर्फ काम के कॉलम ताकि मेमोरी कम खर्च हो
            df_part = pd.read_sql_query("SELECT symbol, date, close FROM stock_data", conn)
            conn.close()
            all_data.append(df_part)
        
        # सभी को एक साथ मिलाना (Merging)
        final_df = pd.concat(all_data, ignore_index=True)
        final_df['date'] = pd.to_datetime(final_df['date'])
        final_df['day_month'] = final_df['date'].dt.strftime('%d-%b')
        return final_df

try:
    df = load_all_data()

    if not df.empty:
        st.success(f"🔱 महाकाल डेटा लोड सफल: {df['symbol'].nunique()} स्टॉक्स का बैकअप तैयार है।")

        # --- TIME CYCLE UI ---
        st.header("📊 परफेक्ट टाइम साइकिल खोज")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_stock = st.selectbox("स्टॉक चुनें", sorted(df['symbol'].unique()))
        with col2:
            cycle_days = st.number_input("साइकिल के दिन (उदा. 90, 180, 365)", value=90)

        # यहाँ आपकी टाइम साइकिल की लॉजिक आएगी
        if st.button("🔱 साइकिल की खोज करें"):
            stock_data = df[df['symbol'] == selected_stock].sort_values('date')
            st.write(f"🔍 {selected_stock} के पिछले 10 साल के डेटा में {cycle_days} दिनों का चक्र देखा जा रहा है...")
            # साइकिल चार्ट और कैलकुलेशन यहाँ डिस्प्ले होंगे
            st.line_chart(stock_data.set_index('date')['close'])

except Exception as e:
    st.error(f"Error: {e}")
