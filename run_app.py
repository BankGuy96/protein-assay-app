import streamlit.web.cli as stcli
import os, sys
import pandas, numpy, sklearn, plotly, xlsxwriter

def resolve_path(path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.path.abspath("."), path)

if __name__ == "__main__":
    target_file = resolve_path("protein_app.py")
    sys.argv = ["streamlit", "run", target_file, "--server.headless", "true", "--global.developmentMode", "false"]
    stcli.main()
