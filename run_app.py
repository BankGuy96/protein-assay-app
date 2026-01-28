import streamlit.web.cli as stcli
import os, sys
import pandas
import numpy
import sklearn
import plotly
import xlsxwriter # สำคัญมากสำหรับปุ่ม Save Excel

def resolve_path(path):
    """ฟังก์ชันช่วยหาตำแหน่งไฟล์ภายในตัว .exe หรือในเครื่อง"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.path.abspath("."), path)

if __name__ == "__main__":
    # ระบุไฟล์หลักที่เราเพิ่งปรับปรุงความสวยงามไป
    target_file = resolve_path("protein_app.py")
    
    # คำสั่งรัน Streamlit ภายในตัว .exe หรือ .bat
    sys.argv = [
        "streamlit",
        "run",
        target_file,
        "--server.headless", "true",
        "--global.developmentMode", "false",
    ]
    sys.exit(stcli.main())
