import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# --- การตั้งค่าหน้าจอและหน้าตา (UI) ---
st.set_page_config(page_title="Pro-Assay Analysis Ultra", layout="wide")

# CSS สำหรับโทนสีเขียวและการอ่านง่ายบนมือถือ
st.markdown("""
    <style>
    /* พื้นหลังเขียวอ่อนไล่เฉด */
    .stApp {
        background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
    }
    
    /* บังคับตัวอักษรพื้นฐานให้เข้มจัดเพื่อให้อ่านง่าย */
    html, body, [class*="st-"] {
        color: #052e16 !important;
        font-family: 'Inter', 'Kanit', sans-serif;
    }

    /* หัวข้อหลัก */
    h1 {
        color: #1b4332 !important;
        font-weight: 800 !important;
        text-align: center;
        text-shadow: 1px 1px 1px rgba(255,255,255,0.8);
    }

    /* หัวข้อรอง */
    h2, h3 {
        color: #2d6a4f !important;
        font-weight: 700 !important;
        border-left: 5px solid #2d6a4f;
        padding-left: 10px;
    }

    /* บังคับปุ่มให้ตัวอักษรสีขาวและเข้ม */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #1b4332 !important;
        border: 2px solid #081c15;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* บังคับตัวหนังสือในปุ่ม (Tag <p>) เป็นสีขาว */
    div.stButton > button p, div.stDownloadButton > button p {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }

    div.stButton > button:hover {
        background-color: #2d6a4f !important;
        transform: scale(1.02);
    }

    /* ปรับปรุง Label ช่องกรอกข้อมูลให้หนาขึ้น */
    label p {
        color: #052e16 !important;
        font-weight: 600 !important;
    }

    /* ปรับพื้นหลัง Expander ให้ขาวสะอาด */
    .streamlit-expanderHeader {
        background-color: white !important;
        border: 1px solid #c8e6c9 !important;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌿 Pro-Assay Analysis (Ultra Edition)")
st.markdown("<center>โปรแกรมวิเคราะห์ความเข้มข้นโปรตีน สำหรับงานวิจัยในแล็บ</center>", unsafe_allow_html=True)

# --- ส่วนที่ 1: การตั้งค่า Assay ---
with st.container():
    st.subheader("📍 1. Assay Configuration")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        assay_type = st.selectbox("Assay Method", ["BCA Assay (A562)", "Bradford Assay (A595)"])
        y_label = "Absorbance (A562)" if "BCA" in assay_type else "Absorbance (A595)"
    with col_b:
        protein_name = st.text_input("Project Name", "Exp_Batch_001")
    with col_c:
        exp_date = st.date_input("Experiment Date")

st.markdown("---")

# --- ส่วนที่ 2: Standard Curve (BSA Triplicate) ---
st.subheader(f"📊 2. Standard Curve (BSA Triplicate)")
with st.expander("📝 คลิกเพื่อกรอกข้อมูล BSA Standard", expanded=True):
    default_bsa = pd.DataFrame({
        'BSA Conc (mg/mL)': [0.0, 0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0],
        'Abs 1': [0.0]*8, 'Abs 2': [0.0]*8, 'Abs 3': [0.0]*8,
        'Blank Abs': [0.0]*8
    })
    
    # ปรับความกว้างคอลัมน์เพื่อเลี่ยงไอคอนทับตัวหนังสือ
    bsa_input = st.data_editor(
        default_bsa, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "BSA Conc (mg/mL)": st.column_config.NumberColumn(width="medium"),
            "Abs 1": st.column_config.NumberColumn(width="small"),
            "Abs 2": st.column_config.NumberColumn(width="small"),
            "Abs 3": st.column_config.NumberColumn(width="small"),
            "Blank Abs": st.column_config.NumberColumn(width="small")
        }
    )

if st.button("📈 วิเคราะห์ Standard Curve"):
    abs_cols = ['Abs 1', 'Abs 2', 'Abs 3']
    # เฉลี่ยเฉพาะช่องที่ไม่เป็น 0 (NaN จะไม่ถูกนำมาคิดค่าเฉลี่ย)
    temp_abs = bsa_input[abs_cols].replace(0, np.nan)
    bsa_input['Avg Abs'] = temp_abs.mean(axis=1)
    bsa_input['Corrected Abs'] = bsa_input['Avg Abs'] - bsa_input['Blank Abs']
    
    clean_bsa = bsa_input.dropna(subset=['Corrected Abs'])
    
    if len(clean_bsa) > 1:
        X = clean_bsa[['BSA Conc (mg/mL)']].values
        y = clean_bsa['Corrected Abs'].values
        model = LinearRegression().fit(X, y)
        r2 = r2_score(y, model.predict(X))
        
        st.session_state.slope = model.coef_[0]
        st.session_state.intercept = model.intercept_
        st.session_state.r2 = r2

        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("Linearity (R²)", f"{r2:.4f}")
            st.success(f"**Equation:** y = {st.session_state.slope:.4f}x + {st.session_state.intercept:.4f}")
            if r2 < 0.98:
                st.warning("⚠️ R² ต่ำกว่า 0.98 ลองเช็กค่าเบี่ยงเบนรายจุด")
        with c2:
            fig = px.scatter(clean_bsa, x='BSA Conc (mg/mL)', y='Corrected Abs', trendline="ols",
                             labels={'Corrected Abs': y_label}, template="plotly_white")
            fig.update_traces(marker=dict(color='#2d6a4f', size=10))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("กรุณากรอกข้อมูล BSA อย่างน้อย 2 จุดขึ้นไป")

st.markdown("---")

# --- ส่วนที่ 3: Sample Analysis (Triplicate Support) ---
st.subheader("🧪 3. Sample Analysis (Triplicate)")
col1, col2 = st.columns([1, 3])
with col1:
    num_samples = st.number_input("จำนวนตัวอย่าง (Samples)", min_value=1, value=3)
    sample_names_raw = st.text_area("รายชื่อตัวอย่าง (แยกด้วยเครื่องหมาย , )", "S1, S2, S3")
    s_list = [s.strip() for s in sample_names_raw.split(',')]
    while len(s_list) < num_samples: s_list.append(f"Sample {len(s_list)+1}")

with col2:
    default_samples = pd.DataFrame({
        'Sample Name': s_list[:num_samples],
        'Dilution Factor': [1.0] * num_samples,
        'Abs 1': [0.0] * num_samples,
        'Abs 2': [0.0] * num_samples,
        'Abs 3': [0.0] * num_samples,
        'Blank Abs': [0.0] * num_samples
    })
    sample_input = st.data_editor(
        default_samples, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "Sample Name": st.column_config.TextColumn(width="medium"),
            "Dilution Factor": st.column_config.NumberColumn(width="small")
        }
    )

if st.button("🧮 คำนวณความเข้มข้นตัวอย่าง"):
    if 'slope' not in st.session_state:
        st.error("❌ ต้องวิเคราะห์ Standard Curve ก่อนคำนวณตัวอย่าง")
    else:
        res = sample_input.copy()
        temp_s_abs = res[['Abs 1', 'Abs 2', 'Abs 3']].replace(0, np.nan)
        res['Avg Abs'] = temp_s_abs.mean(axis=1)
        res['Corrected Abs'] = res['Avg Abs'] - res['Blank Abs']
        
        # คำนวณหาค่า x จาก y (x = (y-c)/m)
        res['Conc (mg/mL)'] = (res['Corrected Abs'] - st.session_state.intercept) / st.session_state.slope
        # ล้างค่าติดลบให้เป็น 0 (กรณี Abs ต่ำกว่า Blank)
        res['Conc (mg/mL)'] = res['Conc (mg/mL)'].apply(lambda x: x if x > 0 else 0)
        res['Final Conc (x Dilution)'] = res['Conc (mg/mL)'] * res['Dilution Factor']
        
        st.write("### 📋 ตารางสรุปผลการวิเคราะห์")
        st.dataframe(res.style.background_gradient(subset=['Final Conc (x Dilution)'], cmap='Greens'), use_container_width=True)

        # บันทึกเป็น Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            res.to_excel(writer, index=False, sheet_name='Sample_Results')
            pd.DataFrame({
                'Parameter': ['Assay Type', 'Date', 'Slope', 'Intercept', 'R-Square'],
                'Value': [assay_type, str(exp_date), st.session_state.slope, st.session_state.intercept, st.session_state.r2]
            }).to_excel(writer, index=False, sheet_name='Calibration_Info')
        
        st.download_button(
            label="📥 ดาวน์โหลดรายงาน Excel",
            data=output.getvalue(),
            file_name=f"Report_{protein_name}_{exp_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
