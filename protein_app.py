import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# --- การตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Pro-Assay Ultra", layout="wide")

# --- CSS ขั้นสูงเพื่อความสวยงามและการซ่อน Text ที่ไม่ต้องการ ---
st.markdown("""
    <style>
    /* 1. พื้นหลังโทนเขียวมินต์ */
    .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); }
    
    /* 2. บังคับฟอนต์เข้มชัดเจน */
    html, body, [class*="st-"] { color: #052e16 !important; font-family: 'Inter', 'Kanit', sans-serif; }

    /* 3. กำจัดตัวหนังสือ arrow_right / arrow_down / arrow_drop_down */
    [data-testid="stExpander"] svg + div { display: none !important; }
    .st-emotion-cache-p5mtransition-element, .st-emotion-cache-1vt4y6f { font-size: 0px !important; color: transparent !important; }
    
    /* 4. ปรับหัวข้อ */
    h1 { color: #1b4332 !important; font-weight: 800 !important; text-align: center; }
    h2, h3 { color: #2d6a4f !important; font-weight: 700 !important; border-left: 6px solid #2d6a4f; padding-left: 12px; }

    /* 5. ปุ่มกด: ฟอนต์ขาวเท่านั้น */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #1b4332 !important;
        border: 2px solid #081c15;
        border-radius: 12px;
        height: 3rem;
    }
    div.stButton > button p, div.stDownloadButton > button p {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }
    div.stButton > button:hover { background-color: #2d6a4f !important; transform: translateY(-2px); }

    /* 6. แก้ไขตารางขาวสะอาด */
    .stDataEditor { background-color: white !important; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌿 Pro-Assay Analysis Ultra")
st.markdown("<p style='text-align: center;'>วิเคราะห์ค่าความเข้มข้นโปรตีนแม่นยำสูง รองรับ Triplicate</p>", unsafe_allow_html=True)

# --- ส่วนที่ 1: Assay Config ---
with st.container():
    st.subheader("📍 1. Assay Information")
    c1, c2, c3 = st.columns(3)
    with c1:
        assay_type = st.selectbox("Method", ["BCA Assay (A562)", "Bradford Assay (A595)"])
        y_label = "Absorbance (A562)" if "BCA" in assay_type else "Absorbance (A595)"
    with c2:
        proj_name = st.text_input("Project Name", "Lab_Batch_01")
    with c3:
        date_val = st.date_input("Date")

st.markdown("---")

# --- ส่วนที่ 2: Standard Curve ---
st.subheader("📊 2. Standard Curve (BSA)")

# ใช้ markdown เพื่อทำตัวหนาและใส่ไอคอน แทนการใช้ expander
st.markdown("#### 📝 กรอกข้อมูล BSA Standard") 

# วางตารางไว้ด้านล่างหัวข้อโดยตรง (ไม่ต้องย่อหน้า)
df_bsa = pd.DataFrame({
    'Conc (mg/mL)': [0.0, 0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0],
    'Abs 1': [0.0]*8, 'Abs 2': [0.0]*8, 'Abs 3': [0.0]*8, 'Blank': [0.0]*8
})

bsa_input = st.data_editor(
    df_bsa, num_rows="dynamic", use_container_width=True,
    column_config={
        "Conc (mg/mL)": st.column_config.NumberColumn(width=130, format="%.3f"),
        "Abs 1": st.column_config.NumberColumn(width=90),
        "Abs 2": st.column_config.NumberColumn(width=90),
        "Abs 3": st.column_config.NumberColumn(width=90),
        "Blank": st.column_config.NumberColumn(width=90)
    }
)

if st.button("📈 วิเคราะห์ Standard Curve"):
    cols = ['Abs 1', 'Abs 2', 'Abs 3']
    temp = bsa_input[cols].replace(0, np.nan)
    bsa_input['Avg'] = temp.mean(axis=1)
    bsa_input['Net'] = bsa_input['Avg'] - bsa_input['Blank']
    clean = bsa_input.dropna(subset=['Net'])
    
    if len(clean) > 1:
        X = clean[['Conc (mg/mL)']].values
        y = clean['Net'].values
        model = LinearRegression().fit(X, y)
        r2 = r2_score(y, model.predict(X))
        st.session_state.m, st.session_state.c, st.session_state.r2 = model.coef_[0], model.intercept_, r2

        sc1, sc2 = st.columns([1, 2])
        with sc1:
            st.metric("R² Score", f"{r2:.4f}")
            st.success(f"y = {st.session_state.m:.4f}x + {st.session_state.c:.4f}")
        with sc2:
            fig = px.scatter(clean, x='Conc (mg/mL)', y='Net', trendline="ols", template="simple_white")
            fig.update_traces(marker=dict(color='#1b4332', size=10))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("กรุณากรอกข้อมูลอย่างน้อย 2 แถว")

st.markdown("---")

# --- ส่วนที่ 3: Sample Analysis ---
st.subheader("🧪 3. Sample Analysis")
scol1, scol2 = st.columns([1, 3])
with scol1:
    n_s = st.number_input("จำนวนตัวอย่าง", min_value=1, value=3)
    s_names = st.text_area("ชื่อตัวอย่าง (แยกด้วย , )", "S1, S2, S3")
    names = [n.strip() for n in s_names.split(',')]
    while len(names) < n_s: names.append(f"Sample {len(names)+1}")

with scol2:
    df_s = pd.DataFrame({
        'Sample Name': names[:n_s], 'Dilution': [1.0]*n_s,
        'Abs 1': [0.0]*n_s, 'Abs 2': [0.0]*n_s, 'Abs 3': [0.0]*n_s, 'Blank': [0.0]*n_s
    })
    s_input = st.data_editor(
        df_s, num_rows="dynamic", use_container_width=True,
        column_config={
            "Sample Name": st.column_config.TextColumn(width=150),
            "Dilution": st.column_config.NumberColumn(width=100)
        }
    )

if st.button("🧮 คำนวณความเข้มข้น"):
    if 'm' not in st.session_state:
        st.error("วิเคราะห์ Standard Curve ก่อนครับ")
    else:
        res = s_input.copy()
        res['Avg'] = res[['Abs 1', 'Abs 2', 'Abs 3']].replace(0, np.nan).mean(axis=1)
        res['Net'] = res['Avg'] - res['Blank']
        res['Conc'] = (res['Net'] - st.session_state.c) / st.session_state.m
        res['Conc'] = res['Conc'].apply(lambda x: x if x > 0 else 0)
        res['Final_Conc'] = res['Conc'] * res['Dilution']
        
        st.write("#### 📋 รายงานผลการวิเคราะห์")
        st.dataframe(res.style.background_gradient(subset=['Final_Conc'], cmap='Greens'), use_container_width=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            res.to_excel(writer, index=False, sheet_name='Results')
            pd.DataFrame({'Metric': ['Slope', 'Intercept', 'R2'], 
                          'Value': [st.session_state.m, st.session_state.c, st.session_state.r2]}).to_excel(writer, index=False, sheet_name='Curve')
        st.download_button("📥 Save to Excel", output.getvalue(), f"Report_{proj_name}.xlsx")

