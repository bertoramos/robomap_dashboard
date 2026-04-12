import streamlit as st
from utils.load_db import load_db

# Set wide layout before any Streamlit UI calls
st.set_page_config(page_title="Dashboard", layout="wide")

# --- Carga de base de datos en el sidebar (compartida para todas las pestañas) ---
with st.sidebar:
    st.header("Database")
    uploaded_file = st.file_uploader("Load SQLite file", type=["sqlite", "sqlite3"])
    if uploaded_file is not None:
        with open("temp_db.sqlite", "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state["tables"] = load_db("temp_db.sqlite")
        st.session_state["db_name"] = uploaded_file.name
        st.success(f"Loaded: {uploaded_file.name}")
    elif "tables" not in st.session_state:
        st.info("No database loaded yet.")

pg = st.navigation([
    st.Page("pages/home.py", title="Home"),
    st.Page("pages/tables_view.py", title="Tables View"),
])
pg.run()
