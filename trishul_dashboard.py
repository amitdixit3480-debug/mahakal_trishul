import streamlit as st
import sqlite3
import pandas as pd
import glob
import os

# 1. पेज सेटअप
st.set_page_config(page_title="Mahakal Time Cycle Scanner", layout="wide")

# 2. मल्टी-पार्ट डेटा लोड करने वाला फंक्शन (बिना .db एक्सटेंशन के लिए अपडेटेड)
@st.cache_data
def load_combined_data():
    all_chunks = []
    # आपकी फ़ाइलों के नाम 'mahakal_part_1' हैं, इसलिए '*' का उपयोग किया है
    db_files = glob.glob("mahakal_part_*")
    
    if not db_files:
        st.error("❌ कोई डेटाबेस पार्ट नहीं मिला! कृपया चेक करें कि फ़ाइलें GitHub पर हैं या नहीं।")
        return pd.DataFrame()

    for file in db_files:
        try:
            # SQLite को बताना कि यह एक डेटाबेस फ़ाइल है भले ही .db न लिखा हो
            conn = sqlite3.connect(file)
            df_part = pd.read_sql_query("SELECT symbol, date, close FROM stock_data", conn)
            conn.close()
            all_chunks.append(df_part)
        except Exception as e:
            st.warning(f"⚠️ {file} को लोड करने में समस्या: {e}")
    
    if all_chunks:
        final_df = pd.concat(all_chunks, ignore_index=True)
        final_df['date'] = pd.to_datetime(final_df['date'])
        return final_df
    return pd.DataFrame()

# --- मुख्य इंटरफ़ेस ---
try:
    st.title("🔱 Mahakal Time Cycle & Seasonal Dashboard")
    
    df = load_combined_data()

    if not df.empty:
        st.sidebar.success(f"✅ {len(df)} रो डेटा सफलतापूर्वक लोड हुआ")
        
        # फिल्टर सेक्शन
        col1, col2 = st.columns(2)
        with col1:
            stock_list = sorted(df['symbol'].unique())
            selected_stock = st.selectbox("🎯 स्टॉक चुनें", stock_list)
        
        with col2:
            cycle_days = st.number_input("⏳ टाइम साइकिल (दिनों में)", value=90, step=1)

        # डेटा प्रोसेसिंग
        stock_df = df[df['symbol'] == selected_stock].sort_values('date')
        
        # चार्ट प्रदर्शन
        st.subheader(f"📈 {selected_stock} का चार्ट और {cycle_days} दिनों का चक्र")
        st.line_chart(stock_df.set_index('date')['close'])

        # --- टाइम साइकिल की खोज (Logic) ---
        st.divider()
        st.subheader("🔍 साइकिल विश्लेषण")
        
        # आखिरी क्लोजिंग और अगली संभावित साइकिल डेट
        last_date = stock_df['date'].max()
        next_cycle_date = last_date + pd.Timedelta(days=cycle_days)
        
        c1, c2 = st.columns(2)
        c1.metric("आखिरी डेटा डेट", last_date.strftime('%d-%b-%Y'))
        c2.metric("अगली संभावित साइकिल तिथि", next_cycle_date.strftime('%d-%b-%Y'))

        st.info(f"🔱 टिप: {selected_stock} में हर {cycle_days} दिन बाद एक बड़ा मूवमेंट आने की संभावना रहती है।")

except Exception as e:
    st.error(f"❌ ऐप चलाने में एरर आया: {e}")
