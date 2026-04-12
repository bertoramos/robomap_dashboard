import streamlit as st

st.title("Home")

st.info("Load a `.sqlite` or `.sqlite3` file from the **sidebar** to get started.")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1. Load database")
    st.caption("Sidebar > Browse files > select your `.sqlite3`")

with col2:
    st.subheader("2. Explore tables")
    st.caption("**Tables View** -- raw content and stats of any table")

with col3:
    st.subheader("3. Analyse captures")
    st.caption("**Capture View** -- summary stats and RSSI heatmap")

st.divider()

with st.expander("Capture View details"):
    st.markdown("""
| Tab | What it does |
|---|---|
| **Summary** | Descriptive stats + per-capture unique MACs, channels, protocols and their counts |
| **Heatmap** | Interpolated RSSI map over (x, y). Filter by MAC, channel, protocol. RSSI averaged per coordinate |
""")

with st.expander("Tips"):
    st.markdown("""
- Replace the loaded file anytime by uploading a new one.
- Filters in Capture View are independent of each other.
- The heatmap uses cubic interpolation with 4+ points, linear with 3, nearest with fewer.
""")

