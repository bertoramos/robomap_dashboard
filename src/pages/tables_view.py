
import streamlit as st

st.header("Tables view")
st.write("In this page, you can view the tables of the database loaded.")

if "tables" not in st.session_state:
    st.warning("No database loaded. Use the sidebar to load a SQLite file.")
else:
    tables = st.session_state["tables"]
    selected_table = st.selectbox("Select a table", list(tables.keys()))
    if selected_table:
        st.subheader(f"Content: {selected_table}")
        st.dataframe(tables[selected_table])

        st.subheader(f"Summary: {selected_table}")
        st.write(tables[selected_table].describe())
