import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap
import pandas as pd

# ----------------------------
# Page config & style
# ----------------------------
st.set_page_config(page_title="🦠 John Snow 1854 Cholera Dashboard", layout="wide")
st.markdown(
    """
    <style>
    .stApp {
        background-color: hotpink;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.title("🦠 John Snow — Cholera Map (Broad Street, London)")

# ----------------------------
# Load shapefiles
# ----------------------------
CHOLERA_SHP = "Cholera_Deaths.shp"
PUMPS_SHP = "Pumps.shp"

def load_and_fix_crs(path):
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return gdf

cholera = load_and_fix_crs(CHOLERA_SHP)
pumps = load_and_fix_crs(PUMPS_SHP)

# ----------------------------
# Sidebar controls
# ----------------------------
st.sidebar.header("Map Controls")
show_deaths = st.sidebar.checkbox("Show Cholera Deaths", True)
show_pumps = st.sidebar.checkbox("Show Pumps", True)
use_cluster = st.sidebar.checkbox("Cluster deaths markers", True)
show_heatmap = st.sidebar.checkbox("Show Heatmap", False)
heat_radius = st.sidebar.slider("Heatmap radius", 5, 50, 15)
basemap_choice = st.sidebar.selectbox("Select basemap", 
                                      ["OpenStreetMap", "CartoDB positron"])

# ----------------------------
# Quick counts
# ----------------------------
st.sidebar.subheader("Summary")
st.sidebar.write(f"- Total deaths: {len(cholera)}")
st.sidebar.write(f"- Total pumps: {len(pumps)}")

# ----------------------------
# Build Folium Map
# ----------------------------
if len(cholera) > 0:
    center_lat = cholera.geometry.y.mean()
    center_lon = cholera.geometry.x.mean()
elif len(pumps) > 0:
    center_lat = pumps.geometry.y.mean()
    center_lon = pumps.geometry.x.mean()
else:
    center_lat, center_lon = 51.5136, -0.1365

m = folium.Map(location=[center_lat, center_lon], zoom_start=16, tiles=basemap_choice)

# Layers
death_layer = folium.FeatureGroup(name="Cholera Deaths", show=show_deaths)
pump_layer = folium.FeatureGroup(name="Pumps", show=show_pumps)

# Cholera Deaths markers
if show_deaths:
    if use_cluster:
        cluster = MarkerCluster(name="Death cluster")
        for _, r in cholera.iterrows():
            folium.Marker(
                location=[r.geometry.y, r.geometry.x],
                popup=folium.Popup("💀 Cholera Death", max_width=150),
                icon=folium.Icon(color="darkred", icon="plus", prefix="fa")
            ).add_to(cluster)
        cluster.add_to(death_layer)
    else:
        for _, r in cholera.iterrows():
            folium.Marker(
                location=[r.geometry.y, r.geometry.x],
                popup=folium.Popup("💀 Cholera Death", max_width=150),
                icon=folium.Icon(color="darkred", icon="plus", prefix="fa")
            ).add_to(death_layer)

# Heatmap
if show_heatmap and show_deaths:
    heat_data = [[r.geometry.y, r.geometry.x] for _, r in cholera.iterrows()]
    HeatMap(heat_data, radius=heat_radius, blur=10).add_to(m)

# Pumps markers
if show_pumps:
    for _, r in pumps.iterrows():
        folium.Marker(
            location=[r.geometry.y, r.geometry.x],
            popup=folium.Popup("🚰 Pump", max_width=150),
            icon=folium.Icon(color="blue", icon="tint", prefix="fa")
        ).add_to(pump_layer)

# Add layers & control
death_layer.add_to(m)
pump_layer.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

# Legend (floating, nampak jelas)
legend_html = """
<div style="position: fixed; bottom: 50px; left: 10px; width:170px; height:90px;
 border:2px solid grey; z-index:9999; font-size:14px; background-color:white; opacity:0.9; padding:8px">
 <b>Legend</b><br>
 <i style="background:darkred; width:10px; height:10px; border-radius:50%; display:inline-block"></i> Deaths<br>
 <i style="background:blue; width:10px; height:10px; display:inline-block"></i> Pumps
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# ----------------------------
# Display map
# ----------------------------
st.subheader("Interactive Map")
st_folium(m, width=1000, height=700)

# ----------------------------
# Data preview
# ----------------------------
st.subheader("Top 5 Cholera Deaths")
st.dataframe(cholera.head())

st.subheader("All Pumps")
st.dataframe(pumps)