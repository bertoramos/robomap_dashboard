
import streamlit as st
import pandas as pd

from components.heatmap import create_heatmap

st.header("Captures view")
st.write("In this page, you can view the captures")

def join_captures(tables):
    b = tables["Beacon_BLE_Signal"].copy()
    c = tables["Capture"].copy().rename(columns={"Id": "Capture_Id"})

    # Equivalent to:
    # FROM Beacon_BLE_Signal b
    # JOIN Capture c ON b.Id_capture = c.Id
    df_joined = b.merge(
        c,
        left_on="Id_capture",
        right_on="Capture_Id",
        how="inner",
    )

    # Equivalent to the SELECT projection + alias b.Id AS Beacon_Id
    result = df_joined.loc[:, [
        "Id",                  # b.Id
        "Id_capture",
        "N_reading",
        "Date_hour",
        "Mac",
        "Pack_size",
        "Channel",
        "RSSI",
        "PDU_type",
        "CRC",
        "Protocol",
        "Identificator",
        "Date",
        "Light",
        "Temperature",
        "Relative_humidity",
        "Absolute_humidity",
        "Position_x",
        "Position_y",
        "Position_z",
        "Platform_angle",
        "Dongle_rotation",
    ]]
    
    return result

def heatmap_tab(captures_df):

    col1, col2, col3 = st.columns(3)
    with col1:
        beacon_options = sorted(captures_df["Mac"].dropna().unique().tolist())
        beacon_default = [beacon_options[0]] if beacon_options else []
        selected_beacons = st.multiselect(
            "Mac",
            beacon_options,
            default=beacon_default,
        )

    with col2:
        channel_options = sorted(captures_df["Channel"].dropna().unique().tolist())
        channel_default = [37] if 37 in channel_options else ([channel_options[0]] if channel_options else [])
        selected_channels = st.multiselect(
            "Channel",
            channel_options,
            default=channel_default,
        )

    with col3:
        protocol_options = sorted(captures_df["Protocol"].dropna().unique().tolist())
        protocol_default = protocol_options[0] if protocol_options else None
        selected_protocol = st.selectbox(
            "Protocol",
            protocol_options,
            index=protocol_options.index(protocol_default) if protocol_default in protocol_options else 0,
        )
    
    if not selected_beacons:
        st.warning("Please select at least one Mac.")
        return

    # select data
    mask = captures_df["Mac"].isin(selected_beacons)
    # filter by multiple selected channels (if any)
    if selected_channels:
        mask &= captures_df["Channel"].isin(selected_channels)
    # filter by protocol if selected
    if selected_protocol is not None:
        mask &= captures_df["Protocol"] == selected_protocol

    df_filtered = captures_df[mask]

    # promediar RSSI por coordenada (x, y)
    df_filtered = df_filtered.groupby(
        ["Position_x", "Position_y"],
        as_index=False,
    ).agg({"RSSI": "mean"})
    puntos = df_filtered[["Position_x", "Position_y", "RSSI"]].values

    fig = create_heatmap(puntos, background_image=None)
    st.plotly_chart(fig, width='stretch')

def summary_tab(captures_df):
    st.write("Summary statistics of the captures:")
    st.write(captures_df.describe())
        
    summary = captures_df.groupby("Id_capture", as_index=False).agg({
        "Mac": lambda s: sorted(pd.unique(s.dropna())),
        "Channel": lambda s: sorted(pd.unique(s.dropna())),
        "Protocol": lambda s: sorted(pd.unique(s.dropna())),
    })
    
    # counts of unique values
    summary["Mac_count"] = summary["Mac"].apply(len)
    summary["Channel_count"] = summary["Channel"].apply(len)
    summary["Protocol_count"] = summary["Protocol"].apply(len)
    
    st.write("Summary by Capture:")
    st.dataframe(summary)

if "tables" not in st.session_state:
    st.warning("No database loaded. Use the sidebar to load a SQLite file.")
else:
    st.subheader("Heatmap")
    # Mostrar filtros
    tables = st.session_state["tables"]
    captures = join_captures(tables)
    
    tabs = st.tabs(["Summary", "Heatmap"])
    
    with tabs[0]:
        st.subheader("Summary")
        summary_tab(captures)
    
    with tabs[1]:
        heatmap_tab(captures)
    
    