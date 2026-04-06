import streamlit as st
import geopandas as gpd
import pandas as pd
import pydeck as pdk
import numpy as np
import osmnx as ox
import os

# ─── 1. PAGE CONFIG & MODERN CSS (EDGE-TO-EDGE) ─────────────────────────────
st.set_page_config(layout="wide", page_title="Vadodara Simulation", page_icon="🌐")

st.markdown("""
<style>
    /* Full screen map resets */
    .block-container { padding: 0 !important; max-width: 100% !important; }
    [data-testid="stHeader"] { display: none; }
    
    /* Floating Glassmorphism Control Panel */
    .floating-panel {
        position: absolute;
        top: 30px;
        left: 30px;
        z-index: 999;
        background: rgba(13, 18, 32, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(59, 124, 244, 0.3);
        border-radius: 16px;
        padding: 24px;
        width: 380px;
        color: white;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    }
    .panel-title {
        font-size: 22px; font-weight: 800; margin-bottom: 5px;
        background: -webkit-linear-gradient(45deg, #3B7CF4, #34D399);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .panel-subtitle { font-size: 12px; color: #8A9EC0; letter-spacing: 1px; margin-bottom: 20px; text-transform: uppercase; }
    
    /* Custom Metric Styling */
    .sim-metric { display: flex; justify-content: space-between; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); }
    .sim-label { font-size: 13px; color: #AECDFE; }
    .sim-value { font-size: 16px; font-weight: 700; color: #FFFFFF; }
    .sim-value.danger { color: #F87171; }
</style>
""", unsafe_allow_html=True)

# ─── 2. DATA LOADING & KNOWLEDGE GRAPH CONSTRUCTION ───────────────────────
FILE_PATH = "/home/ethan/Downloads/URBAN-INEQUALITY-IN-BARODA/data/processed/vadodara_final_uoi_balanced.gpkg"
ROADS_CSV = "/home/ethan/Downloads/URBAN-INEQUALITY-IN-BARODA/data/processed/swmm_road_failures.csv"

@st.cache_data(show_spinner=False)
def load_simulation_data():
    # 1. Load Wards
    wards = gpd.read_file(FILE_PATH, layer="gnn_bym2_results").to_crs(epsg=4326)
    
    # Resolve dynamic column names
    ward_col = next((c for c in ["Ward_Name", "ward_name", "name"] if c in wards.columns), wards.columns[0])
    wards['Ward'] = wards[ward_col]
    
    # 2. Build the "Knowledge Graph" (Road Network + SWMM Results)
    swmm_df = pd.read_csv(ROADS_CSV)
    
    # Fetch original road geometries to draw the graph
    cf = '["highway"~"primary|secondary|tertiary|trunk"]'
    G = ox.graph_from_place("Vadodara, Gujarat, India", network_type='drive', custom_filter=cf, simplify=True)
    nodes, edges = ox.graph_to_gdfs(G)
    
    edges = edges.reset_index()
    # Merge geometries with SWMM hydraulic failures
    graph_edges = edges.merge(swmm_df, on=['u', 'v', 'key'], how='inner').to_crs(epsg=4326)
    graph_nodes = nodes.to_crs(epsg=4326).reset_index()
    
    # Identify flooded nodes (junctions connected to flooded roads)
    flooded_nodes = set(graph_edges[graph_edges['is_flooded'] == 1]['u']).union(
                    set(graph_edges[graph_edges['is_flooded'] == 1]['v']))
    graph_nodes['is_flooded'] = graph_nodes['osmid'].apply(lambda x: 1 if x in flooded_nodes else 0)
    
    # Pydeck requires coordinate lists for lines
    def extract_path(geom):
        if geom.geom_type == 'LineString': return list(geom.coords)
        if geom.geom_type == 'MultiLineString': return list(geom.geoms[0].coords)
        return []
    
    graph_edges['path'] = graph_edges.geometry.apply(extract_path)
    graph_nodes['lon'] = graph_nodes.geometry.x
    graph_nodes['lat'] = graph_nodes.geometry.y
    
    return wards, graph_edges, graph_nodes

with st.spinner("Constructing Urban Knowledge Graph & Simulating Hydraulics..."):
    wards, roads, nodes = load_simulation_data()

# ─── 3. UI STATE & INTERACTIVITY ──────────────────────────────────────────
# Inject the floating panel using standard Streamlit components wrapped in our CSS
st.markdown('<div class="floating-panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">System Simulation</div>', unsafe_allow_html=True)
st.markdown('<div class="panel-subtitle">Hydraulic & Spatial Network Analysis</div>', unsafe_allow_html=True)

# THE INTERACTIVE TOGGLE
phase = st.radio(
    "SIMULATION STATE",
    ["01. Baseline (Healthy Network)", "02. Cloudburst Event (Flooded)", "03. Spatial Opportunity Drag"],
    label_visibility="collapsed"
)

st.markdown('<hr style="border-color: rgba(255,255,255,0.1); margin: 15px 0;">', unsafe_allow_html=True)

# Dynamic Metrics based on Phase
if "01" in phase:
    st.markdown('<div class="sim-metric"><span class="sim-label">Network Status</span><span class="sim-value" style="color:#34D399;">OPTIMAL</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sim-metric"><span class="sim-label">Active Edges (Roads)</span><span class="sim-value">{len(roads):,}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sim-metric"><span class="sim-label">Avg Opportunity Score</span><span class="sim-value">{wards["UOI_Score"].mean():.1f}</span></div>', unsafe_allow_html=True)

elif "02" in phase:
    failed_edges = roads['is_flooded'].sum()
    st.markdown('<div class="sim-metric"><span class="sim-label">Network Status</span><span class="sim-value danger">CRITICAL FAILURE</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sim-metric"><span class="sim-label">Failed Edges (Roads)</span><span class="sim-value danger">{failed_edges:,}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sim-metric"><span class="sim-label">Max Water Depth</span><span class="sim-value danger">{roads["max_depth"].max():.2f}m</span></div>', unsafe_allow_html=True)

else:
    spatial_drag = wards['bym2_spatial_phi'].mean()
    st.markdown('<div class="sim-metric"><span class="sim-label">Network Status</span><span class="sim-value" style="color:#FBBF24;">DEGRADED</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sim-metric"><span class="sim-label">Avg Opportunity Score</span><span class="sim-value" style="color:#FBBF24;">{wards["hybrid_opportunity_score"].mean():.1f}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sim-metric"><span class="sim-label">Systemic Spatial Drag</span><span class="sim-value danger">{spatial_drag:.2f} σ</span></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True) # End floating panel

# ─── 4. PYDECK VISUALIZATION LOGIC ────────────────────────────────────────
# Normalize Data for colors
wards['norm_uoi'] = (wards['UOI_Score'] - wards['UOI_Score'].min()) / (wards['UOI_Score'].max() - wards['UOI_Score'].min())
wards['norm_hyb'] = (wards['hybrid_opportunity_score'] - wards['hybrid_opportunity_score'].min()) / (wards['hybrid_opportunity_score'].max() - wards['hybrid_opportunity_score'].min())
wards['norm_fld'] = (wards['swmm_flood_road_pct'] - wards['swmm_flood_road_pct'].min()) / (wards['swmm_flood_road_pct'].max() - wards['swmm_flood_road_pct'].min() + 1e-6)

# Phase 1: Baseline
if "01" in phase:
    # Wards: Deep Blue to Cyan based on UOI
    wards['fill_color'] = wards['norm_uoi'].apply(lambda x: [10, 30 + (x*100), 50 + (x*200), 100])
    wards['elevation'] = wards['UOI_Score'] * 20
    # Roads: Faint Cyan Knowledge Graph
    roads['color'] = [[59, 124, 244, 100]] * len(roads)
    roads['width'] = 2
    # Nodes: Small glowing dots
    nodes['color'] = [[174, 205, 254, 150]] * len(nodes)
    nodes['radius'] = 15

# Phase 2: The Flood / Shock
elif "02" in phase:
    # Wards: Dimmed, extruded by flood impact
    wards['fill_color'] = wards['norm_fld'].apply(lambda x: [30 + (x*150), 10, 20, 180] if x > 0 else [10, 15, 25, 80])
    wards['elevation'] = wards['swmm_flood_road_pct'] * 150
    # Roads: Red for flooded, dark grey for safe
    roads['color'] = roads['is_flooded'].apply(lambda x: [255, 50, 50, 255] if x else [50, 60, 80, 80])
    roads['width'] = roads['is_flooded'].apply(lambda x: 8 if x else 1)
    # Nodes: Red pulses for flooded junctions
    nodes['color'] = nodes['is_flooded'].apply(lambda x: [255, 80, 80, 255] if x else [50, 60, 80, 50])
    nodes['radius'] = nodes['is_flooded'].apply(lambda x: 40 if x else 5)

# Phase 3: Spatial Impact (GNN + BYM2)
else:
    # Wards: Colored by Hybrid Opportunity (Red = low, Green = high)
    wards['fill_color'] = wards['norm_hyb'].apply(lambda x: [255*(1-x), 200*x, 100, 150])
    wards['elevation'] = wards['hybrid_opportunity_score'] * 20
    # Roads: Ghosted red where damage occurred to show the "memory" of the flood
    roads['color'] = roads['is_flooded'].apply(lambda x: [255, 50, 50, 100] if x else [30, 40, 50, 30])
    roads['width'] = roads['is_flooded'].apply(lambda x: 4 if x else 1)
    nodes['color'] = [[0,0,0,0]] * len(nodes) # Hide nodes for cleaner view
    nodes['radius'] = 0

# ─── 5. BUILD MAP LAYERS ──────────────────────────────────────────────────
# 1. Ward Polygons
layer_wards = pdk.Layer(
    "GeoJsonLayer",
    wards,
    pickable=True,
    stroked=True,
    filled=True,
    extruded=True,
    wireframe=True,
    get_elevation="elevation",
    get_fill_color="fill_color",
    get_line_color=[255, 255, 255, 40],
)

# 2. Road Network (The Knowledge Graph Edges)
layer_roads = pdk.Layer(
    "PathLayer",
    roads,
    pickable=True,
    get_path="path",
    get_color="color",
    width_scale=1,
    width_min_pixels=1,
    get_width="width",
)

# 3. Junction Nodes (The Knowledge Graph Vertices)
layer_nodes = pdk.Layer(
    "ScatterplotLayer",
    nodes,
    get_position=["lon", "lat"],
    get_fill_color="color",
    get_radius="radius",
    radius_min_pixels=2,
    radius_max_pixels=10,
)

# Compile Deck
deck = pdk.Deck(
    layers=[layer_wards, layer_roads, layer_nodes],
    initial_view_state=pdk.ViewState(
        latitude=22.3, longitude=73.18, zoom=12.2, pitch=55, bearing=-20
    ),
    map_style="mapbox://styles/mapbox/dark-v11",
    tooltip={
        "html": "<b>Ward:</b> {Ward}<br/><b>UOI Score:</b> {UOI_Score}<br/><b>Flood Impact:</b> {swmm_flood_road_pct}%",
        "style": {"backgroundColor": "#0D1220", "color": "white", "border": "1px solid #3B7CF4"}
    }
)

# Render edge-to-edge
st.pydeck_chart(deck, use_container_width=True)