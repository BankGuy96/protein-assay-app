import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# --- UI Customization: Green Soft Tone ---
st.set_page_config(page_title="Pro-Assay ", layout="wide")

st.markdown("""
    <style>
    /* พื้นหลังเขียวอ่อนคงเดิม แต่เพิ่มความชัดของฟอนต์ */
    .stApp {
        background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
    }
    
    /* บังคับตัวอักษรทุกจุดให้เป็นสีเข้มจัด */
    html, body, [class*="st-"] {
        color: #052e16 !important; /* สีเขียวเข้มเกือบดำ */
        font-family: 'Inter', 'Kanit', sans-serif;
        font-weight: 500; /* เพิ่มความหนาเริ่มต้น */
    }

    /* หัวข้อหลักให้เด่นสุดๆ */
    h1 {
        color: #1b4332 !important;
        font-weight: 800 !important;
        text-shadow: 1px 1px 1px rgba(255,255,255,0.8);
    }

    /* หัวข้อรอง (Subheader) */
    h2, h3 {
        color: #2d6a4f !important;
        font-weight: 700 !important;
        border-left: 5px solid #2d6a4f;
        padding-left: 10px;
    }

    /* ปรับแต่งตารางให้ตัวเลขชัดเจนบนมือถือ */
    .stDataFrame div[data-testid="stTable"] {
        background-color: white;
        color: black !important;
    }
    
    /* ปรับแต่ง Label ของช่องกรอกข้อมูล */
    label p {
        color: #052e16 !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }

    /* ปรับแต่งปุ่มกดให้คมชัดและตัวอักษรสีขาว */
    .stButton>button {
        background-color: #1b4332 !important; /* พื้นหลังเขียวเข้มจัด */
        color: #ffffff !important;           /* ตัวอักษรสีขาวบริสุทธิ์ */
        border: 2px solid #081c15;
        font-size: 1.15rem !important;      /* ขยายขนาดตัวอักษรเล็กน้อย */
        font-weight: 700 !important;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    
    /* เอฟเฟกต์ตอนเอาเมาส์วาง หรือกดปุ่ม */
    .stButton>button:hover {
        background-color: #2d6a4f !important; /* สว่างขึ้นเล็กน้อยตอนชี้ */
        color: #f1f8e9 !important;           /* ตัวอักษรเปลี่ยนเป็นสีเขียวอ่อนนวลๆ */
        border-color: #4caf50;
        transform: scale(1.02);              /* ขยายปุ่มเล็กน้อยให้ดูมีมิติ */
    }

    /* ปรับแต่งปุ่ม Download (ซึ่งใช้ Tag ต่างกันใน Streamlit) */
    .stDownloadButton>button {
        background-color: #2d6a4f !important;
        color: #ffffff !important;
        border-radius: 12px;
        font-weight: 700;
        width: 100%;
    }
    
    /* ช่อง Expander ให้พื้นหลังขาวสะอาดเพื่อขับตัวหนังสือ */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        border: 1px solid #c8e6c9 !important;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌿 Pro-Assay Analysis (Green Edition)")
st.markdown("<p style='text-align: center; color: #666;'>โปรแกรมวิเคราะห์ความเข้มข้นโปรตีน </p>", unsafe_allow_html=True)

# --- ส่วนที่ 1: ข้อมูลทั่วไป ---
with st.container():
    st.subheader("📍 1. Assay Information")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        assay_type = st.selectbox("Method Selection", ["BCA Assay (A562)", "Bradford Assay (A595)"])
        y_label = "Absorbance (A562)" if "BCA" in assay_type else "Absorbance (A595)"
    with col_b:
        protein_name = st.text_input("Experiment Name", "Green_Lab_Batch_01")
    with col_c:
        exp_date = st.date_input("Date")

st.markdown("---")

# --- ส่วนที่ 2: Standard Curve ---
st.subheader(f"📊 2. Standard Curve (BSA Triplicate)")
with st.expander("📝 คลิกเพื่อกรอกข้อมูล BSA", expanded=True):
    default_bsa = pd.DataFrame({
        'BSA Conc (mg/mL)': [0.0, 0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0],
        'Abs 1': [0.0]*8, 'Abs 2': [0.0]*8, 'Abs 3': [0.0]*8,
        'Blank Abs': [0.0]*8
    })
    bsa_input = st.data_editor(default_bsa, num_rows="dynamic", use_container_width=True)

if st.button("📈 วิเคราะห์และสร้างกราฟ"):
    abs_cols = ['Abs 1', 'Abs 2', 'Abs 3']
    temp_abs = bsa_input[abs_cols].replace(0, np.nan)
    bsa_input['Avg Abs'] = temp_abs.mean(axis=1)
    bsa_input['Corrected Abs'] = bsa_input['Avg Abs'] - bsa_input['Blank Abs']
    
    clean_bsa = bsa_input.dropna(subset=['Corrected Abs'])
    X = clean_bsa[['BSA Conc (mg/mL)']].values
    y = clean_bsa['Corrected Abs'].values
    
    if len(clean_bsa) > 1:
        model = LinearRegression().fit(X, y)
        r2 = r2_score(y, model.predict(X))
        st.session_state.slope, st.session_state.intercept, st.session_state.r2 = model.coef_[0], model.intercept_, r2

        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("R-Squared (Lineatity)", f"{r2:.4f}")
            st.success(f"**Equation:** y = {st.session_state.slope:.4f}x + {st.session_state.intercept:.4f}")
            if r2 < 0.98:
                st.warning("💡 ค่า R² ต่ำกว่า 0.98 แนะนำให้ตรวจสอบ Error ของแต่ละจุด")
        with c2:
            fig = px.scatter(clean_bsa, x='BSA Conc (mg/mL)', y='Corrected Abs', 
                             trendline="ols", color_discrete_sequence=['#2e7d32'])
            fig.update_layout(title="Standard Curve Linearity", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("กรุณากรอกข้อมูล BSA อย่างน้อย 2 จุดขึ้นไป")

st.markdown("---")

# --- ส่วนที่ 3: Sample Analysis ---
st.subheader("🧪 3. Sample Analysis (Triplicate Support)")
col1, col2 = st.columns([1, 3])
with col1:
    num_samples = st.number_input("Total Samples", min_value=1, value=3)
    sample_names = st.text_area("Sample Names (separate with , )", "Sample 1, Sample 2, Sample 3")
    s_list = [s.strip() for s in sample_names.split(',')]
    while len(s_list) < num_samples: s_list.append(f"Unknown {len(s_list)+1}")

with col2:
    default_samples = pd.DataFrame({
        'Sample Name': s_list[:num_samples],
        'Dilution Factor': [1.0] * num_samples,
        'Abs 1': [0.0] * num_samples, 'Abs 2': [0.0] * num_samples, 'Abs 3': [0.0] * num_samples,
        'Blank Abs': [0.0] * num_samples
    })
    sample_input = st.data_editor(default_samples, num_rows="dynamic", use_container_width=True)

if st.button("🧮 คำนวณความเข้มข้น"):
    if 'slope' not in st.session_state:
        st.error("❌ กรุณาสร้าง Standard Curve ให้สำเร็จก่อน")
    else:
        res = sample_input.copy()
        temp_s_abs = res[['Abs 1', 'Abs 2', 'Abs 3']].replace(0, np.nan)
        res['Avg Abs'] = temp_s_abs.mean(axis=1)
        res['Corrected Abs'] = res['Avg Abs'] - res['Blank Abs']
        
        res['Conc (mg/mL)'] = (res['Corrected Abs'] - st.session_state.intercept) / st.session_state.slope
        res['Final Conc (x Dilution)'] = res['Conc (mg/mL)'] * res['Dilution Factor']
        
        st.write("#### 📋 สรุปผลการวิเคราะห์")
        st.dataframe(res.style.background_gradient(subset=['Final Conc (x Dilution)'], cmap='Greens'), use_container_width=True)

        # Download Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            res.to_excel(writer, index=False, sheet_name='Sample_Analysis')
            pd.DataFrame({'Parameter': ['Slope', 'Intercept', 'R-Square'], 
                          'Value': [st.session_state.slope, st.session_state.intercept, st.session_state.r2]}).to_excel(writer, index=False, sheet_name='Calibration_Data')
        
        st.download_button("📥 Save Report to Excel", output.getvalue(), f"Protein_Analysis_{exp_date}.xlsx")



