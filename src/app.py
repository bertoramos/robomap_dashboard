import streamlit as st
from utils.load_db import load_db

# Set wide layout before any Streamlit UI calls
st.set_page_config(page_title="Dashboard", layout="wide")

# --- Shared database loading from sidebar ---
with st.sidebar:
    st.header("Database")
    uploaded_file = st.file_uploader("Load SQLite file", type=["sqlite", "sqlite3"])
    if uploaded_file is not None:
        st.session_state["tables"] = load_db(uploaded_file.getvalue())
        st.session_state["db_name"] = uploaded_file.name
        st.success(f"Loaded: {uploaded_file.name}")
    elif "tables" not in st.session_state:
        st.info("No database loaded yet.")

pg = st.navigation([
    st.Page("pages/home.py", title="Home"),
    st.Page("pages/tables_view.py", title="Tables View"),
])
pg.run()
