import geopandas as gpd
import folium
import osmnx as ox
import json
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WARD_GPKG = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")
RAW_GPKG = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km.gpkg")
BUS_JSON = os.path.join(BASE_DIR, "data", "City-bus", "all_stops.json")

OUTPUT_DIR = os.path.join(BASE_DIR, "results", "interactive_network_maps")
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_HTML = os.path.join(OUTPUT_DIR, "Vadodara_Road_Bus_Network.html")

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
wards = gpd.read_file(WARD_GPKG).to_crs("EPSG:4326")
boundary = gpd.read_file(RAW_GPKG, layer="boundary").to_crs("EPSG:4326")

center = boundary.geometry.iloc[0].centroid

# --------------------------------------------------
# BASE MAP
# --------------------------------------------------
m = folium.Map(location=[center.y, center.x], zoom_start=12, tiles=None)

# Satellite + Physical
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri World Imagery",
    name="Satellite",
    overlay=False,
).add_to(m)

folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    attr="Esri Topographic",
    name="Physical / Terrain",
    overlay=False,
).add_to(m)

# --------------------------------------------------
# ROAD NETWORK (OSMnx)
# --------------------------------------------------
print("→ Loading road network...")
G = ox.graph_from_polygon(boundary.geometry.iloc[0], network_type="drive")
edges = ox.graph_to_gdfs(G, nodes=False).to_crs("EPSG:4326")

road_layer = folium.FeatureGroup(name="Road Network", show=True)

for geom in edges.geometry:
    folium.PolyLine(
        locations=[(y, x) for x, y in geom.coords],
        color="#2b8cbe",
        weight=1,
        opacity=0.35,
    ).add_to(road_layer)

road_layer.add_to(m)

# --------------------------------------------------
# BUS STOPS (ROBUST PARSING)
# --------------------------------------------------
print("→ Loading bus stops...")
with open(BUS_JSON, "r") as f:
    raw = json.load(f)

df = gpd.GeoDataFrame(raw)

coord_col = None
for c in df.columns:
    sample = df[c].astype(str)
    if sample.str.contains(r"\d+\.\d+\s+\d+\.\d+").any():
        coord_col = c
        break

coords = df[coord_col].astype(str).str.extract(r"(?P<lon>\d+\.\d+)\s+(?P<lat>\d+\.\d+)")

df["lon"] = coords["lon"].astype(float)
df["lat"] = coords["lat"].astype(float)

bus = gpd.GeoDataFrame(
    df.dropna(subset=["lon", "lat"]),
    geometry=gpd.points_from_xy(df.lon, df.lat),
    crs="EPSG:4326",
)

bus_layer = folium.FeatureGroup(name="Bus Stops", show=True)

for _, r in bus.iterrows():
    folium.CircleMarker(
        location=[r.geometry.y, r.geometry.x],
        radius=2.5,
        color="#de2d26",
        fill=True,
        fill_opacity=0.9,
        popup=str(r.get("POI_NAME", "Bus Stop")),
    ).add_to(bus_layer)

bus_layer.add_to(m)

# --------------------------------------------------
# WARDS
# --------------------------------------------------
folium.GeoJson(
    wards,
    name="Wards",
    style_function=lambda x: {
        "fillColor": "transparent",
        "color": "#000000",
        "weight": 1,
    },
).add_to(m)

# --------------------------------------------------
# CONTROLS
# --------------------------------------------------
folium.LayerControl(collapsed=False).add_to(m)

# --------------------------------------------------
# SAVE
# --------------------------------------------------
m.save(OUTPUT_HTML)
print(f"✅ Interactive network map saved:\n{OUTPUT_HTML}")
