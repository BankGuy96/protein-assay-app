import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import plotly.express as px
from io import BytesIO

# --- 1. Page Configuration ---
st.set_page_config(page_title="Pro-Assay Ultra", layout="wide")

# --- 2. Advanced CSS (UI & Text Cleaning) ---
st.markdown("""
    <style>
    /* พื้นหลังสีเขียวอ่อน */
    .stApp { background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); }
    
    /* บังคับตัวอักษรเข้มจัดเพื่อให้อ่านง่ายบนมือถือ */
    html, body, [class*="st-"] { color: #052e16 !important; font-family: 'Inter', 'Kanit', sans-serif; }

    /* ซ่อนตัวหนังสือระบบที่ไม่ต้องการ (arrow_right/down) */
    [data-testid="stExpander"] svg + div, 
    .st-emotion-cache-p5mtransition-element,
    .st-emotion-cache-1vt4y6f { 
        display: none !important; 
    }
    
    /* หัวข้อ */
    h1 { color: #1b4332 !important; font-weight: 800 !important; text-align: center; }
    h2, h3 { color: #2d6a4f !important; font-weight: 700 !important; border-left: 6px solid #2d6a4f; padding-left: 12px; }

    /* ปรับแต่งปุ่ม: พื้นหลังเขียวเข้ม ฟอนต์ขาว */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #1b4332 !important;
        border: 2px solid #081c15;
        border-radius: 12px;
        height: 3.5rem;
    }
    div.stButton > button p, div.stDownloadButton > button p {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.15rem !important;
    }
    div.stButton > button:hover { background-color: #2d6a4f !important; transform: scale(1.02); }

    /* ตารางขาวสะอาด */
    .stDataEditor { background-color: white !important; border-radius: 10px; border: 1px solid #c8e6c9; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌿 Pro-Assay Analysis Ultra")

# --- 3. Assay Information ---
st.subheader("📍 1. Assay Information")
c1, c2, c3 = st.columns(3)
with c1:
    assay_type = st.selectbox("Method Selection", ["BCA Assay (A562)", "Bradford Assay (A595)"])
with c2:
    proj_name = st.text_input("Project Name", "Trial_Batch_01")
with c3:
    date_val = st.date_input("Analysis Date")

st.markdown("---")

# --- 4. Standard Curve Section ---
st.subheader("📊 2. Standard Curve (BSA)")
st.markdown("**📝 กรอกข้อมูล BSA Standard**")

df_bsa = pd.DataFrame({
    'Conc (mg/mL)': [0.0, 0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0],
    'Abs 1': [0.0]*8, 'Abs 2': [0.0]*8, 'Abs 3': [0.0]*8, 'Blank': [0.0]*8
})

bsa_input = st.data_editor(
    df_bsa, num_rows="dynamic", use_container_width=True,
    column_config={
        "Conc (mg/mL)": st.column_config.NumberColumn("Conc (mg/mL)", width=130, format="%.3f"),
        "Abs 1": st.column_config.NumberColumn(width=90),
        "Abs 2": st.column_config.NumberColumn(width=90),
        "Abs 3": st.column_config.NumberColumn(width=90),
        "Blank": st.column_config.NumberColumn(width=90)
    }
)

if st.button("📈 วิเคราะห์ Standard Curve"):
    temp_bsa = bsa_input[['Abs 1', 'Abs 2', 'Abs 3']].replace(0, np.nan)
    bsa_input['Average Absorbance'] = temp_bsa.mean(axis=1)
    bsa_input['Net (Avg Abs - Blank)'] = bsa_input['Average Absorbance'] - bsa_input['Blank']
    
    clean_bsa = bsa_input.dropna(subset=['Net (Avg Abs - Blank)'])
    
    if len(clean_bsa) > 1:
        X = clean_bsa[['Conc (mg/mL)']].values
        y = clean_bsa['Net (Avg Abs - Blank)'].values
        model = LinearRegression().fit(X, y)
        r2 = r2_score(y, model.predict(X))
        
        st.session_state.m, st.session_state.c, st.session_state.r2 = model.coef_[0], model.intercept_, r2

        sc1, sc2 = st.columns([1, 2])
        with sc1:
            st.metric("R² (Linearity)", f"{r2:.4f}")
            st.success(f"**สมการ:** y = {st.session_state.m:.4f}x + {st.session_state.c:.4f}")
        with sc2:
            fig = px.scatter(clean_bsa, x='Conc (mg/mL)', y='Net (Avg Abs - Blank)', 
                             trendline="ols", template="simple_white",
                             labels={'Net (Avg Abs - Blank)': 'Net Absorbance'})
            fig.update_traces(marker=dict(color='#1b4332', size=10))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("กรุณากรอกข้อมูลอย่างน้อย 2 แถวเพื่อคำนวณกราฟ")

st.markdown("---")

# --- 5. Sample Analysis Section ---
st.subheader("🧪 3. Sample Analysis")
st.markdown("**📝 กรอกข้อมูลตัวอย่างที่ต้องการวิเคราะห์**")

scol1, scol2 = st.columns([1, 3])
with scol1:
    num_s = st.number_input("จำนวนตัวอย่าง", min_value=1, value=3)
    s_names_raw = st.text_area("รายชื่อตัวอย่าง (แยกด้วย , )", "Sample 1, Sample 2, Sample 3")
    names_list = [n.strip() for n in s_names_raw.split(',')]
    while len(names_list) < num_s: names_list.append(f"S{len(names_list)+1}")

with scol2:
    df_sample = pd.DataFrame({
        'Sample Name': names_list[:num_s],
        'Dilution': [1.0]*num_s,
        'Abs 1': [0.0]*num_s, 'Abs 2': [0.0]*num_s, 'Abs 3': [0.0]*num_s,
        'Blank': [0.0]*num_s
    })
    sample_input = st.data_editor(
        df_sample, num_rows="dynamic", use_container_width=True,
        column_config={
            "Sample Name": st.column_config.TextColumn(width=150),
            "Dilution": st.column_config.NumberColumn(width=100)
        }
    )

if st.button("🧮 คำนวณความเข้มข้นตัวอย่าง"):
    if 'm' not in st.session_state:
        st.error("❌ กรุณากดปุ่ม 'วิเคราะห์ Standard Curve' ก่อน")
    else:
        res = sample_input.copy()
        temp_s = res[['Abs 1', 'Abs 2', 'Abs 3']].replace(0, np.nan)
        res['Average Absorbance'] = temp_s.mean(axis=1)
        res['Net (Avg Abs - Blank)'] = res['Average Absorbance'] - res['Blank']
        
        # คำนวณ x = (y - c) / m
        res['Conc (mg/mL)'] = ((res['Net (Avg Abs - Blank)'] - st.session_state.c) / st.session_state.m).clip(lower=0)
        res['Final Conc (mg/mL)'] = res['Conc (mg/mL)'] * res['Dilution']
        
        st.write("### 📋 ตารางรายงานผลการวิเคราะห์")
        # แสดงตารางพร้อมระบายสี Gradient
        st.dataframe(
            res.style.background_gradient(subset=['Final Conc (mg/mL)'], cmap='Greens'), 
            use_container_width=True
        )

        # Download Report
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            res.to_excel(writer, index=False, sheet_name='Sample_Analysis')
            pd.DataFrame({
                'Parameter': ['Slope (m)', 'Intercept (c)', 'R-Square', 'Date'],
                'Value': [st.session_state.m, st.session_state.c, st.session_state.r2, str(date_val)]
            }).to_excel(writer, index=False, sheet_name='Calibration_Info')
        
        st.download_button(
            label="📥 ดาวน์โหลดรายงานผล (Excel)",
            data=output.getvalue(),
            file_name=f"Protein_Report_{proj_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
