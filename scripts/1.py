import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt

# --- 1. CONFIGURATION ---
# Use the cache so you don't re-download every time you run the script
ox.settings.use_cache = True
ox.settings.log_console = True

print("Fetching data from OSM...")

# --- 2. DOWNLOAD & CLEAN AUTOMATICALLY ---
# ox.graph_from_place() is powerful. 
# network_type='drive' AUTOMATICALLY filters out footways, cycleways, etc.
# simplifying=True cleans up complex intersections (great for routing).
G = ox.graph_from_place(
    "Vadodara, India", 
    network_type="drive", 
    simplify=True
)

print(f"Downloaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")

# --- 3. REPROJECT (CRITICAL) ---
# Project the graph from Lat/Long (WGS84) to UTM Zone 43N (Meters)
# OSMnx does this automatically based on the location's centroid.
G_proj = ox.project_graph(G)

# Alternatively, to force specific EPSG:32643 (Vadodara standard):
# G_proj = ox.project_graph(G, to_crs="EPSG:32643")

# --- 4. CONVERT TO GEODATAFRAME ---
# This converts the graph into standard table format (nodes and lines)
# so we can save it as a layer for QGIS.
nodes, edges = ox.graph_to_gdfs(G_proj)

# --- 5. VISUAL CHECK ---
print("Plotting network...")
fig, ax = ox.plot_graph(G_proj, node_size=0, edge_color="w", edge_linewidth=0.5)

# --- 6. SAVE DATA ---
# A. Save as GraphML (CRITICAL for Python Analysis later)
# This keeps the routing topology (connections).
ox.save_graphml(G_proj, "vadodara_network_drive.graphml")

# B. Save as GeoPackage (for QGIS viewing/mapping)
# This is just the lines for your maps.
edges.to_file("vadodara_roads.gpkg", layer="roads", driver="GPKG")

print("Success! Files saved:")
print(" - vadodara_network_drive.graphml (Use this for Analysis/Routing)")
print(" - vadodara_roads.gpkg (Use this for Mapping/QGIS)")