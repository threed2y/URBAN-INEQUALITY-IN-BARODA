import geopandas as gpd
import pandas as pd
import osmnx as ox
import networkx as nx
import os

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(BASE_DIR, "data", "interim", "vadodara_project.gpkg")
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "processed", "ward_accessibility.csv")
OUTPUT_GPKG = os.path.join(BASE_DIR, "data", "processed", "vadodara_results.gpkg")

# Constants
TARGET_CRS = "EPSG:32643"  # UTM Zone 43N
WALK_SPEED = 4.5  # km/h
DRIVE_SPEED = 30  # km/h (Conservative city average)

print("--- STEP 2: NETWORK ANALYSIS & ACCESSIBILITY ---")

# 1. SETUP & DATA LOADING
print("1. Loading Spatial Database...")
if not os.path.exists(os.path.dirname(OUTPUT_CSV)):
    os.makedirs(os.path.dirname(OUTPUT_CSV))

try:
    wards = gpd.read_file(INPUT_GPKG, layer="wards")
    hospitals = gpd.read_file(INPUT_GPKG, layer="hospitals")
    schools = gpd.read_file(INPUT_GPKG, layer="schools")
    transport = gpd.read_file(INPUT_GPKG, layer="transport")
except Exception as e:
    print(f"❌ Error loading layers: {e}")
    exit()

# 2. DOWNLOAD ROAD NETWORK
print("2. Downloading Vadodara Road Network (this may take 2-3 mins)...")
# We use 'drive' network which is cleaner. We will simulate walking on these roads.
G = ox.graph_from_place("Vadodara, India", network_type="drive")

print("   - Reprojecting network to UTM Zone 43N...")
G = ox.project_graph(G, to_crs=TARGET_CRS)

# 3. ANALYSIS ENGINE
def calculate_access_time(graph, origins, destinations, speed_kmh, name):
    """
    Calculates the average time (minutes) from each Ward Centroid 
    to the Nearest Service point.
    """
    print(f"   - Analyzing {name} (Speed: {speed_kmh} km/h)...")
    
    # Calculate Travel Speed in Meters/Minute
    speed_mpm = (speed_kmh * 1000) / 60
    
    # Get Centroids (This creates the temporary geometry column)
    origins['centroid'] = origins.geometry.centroid
    
    # Snap points to the network nodes
    origin_nodes = ox.nearest_nodes(graph, origins.centroid.x, origins.centroid.y)
    dest_nodes = ox.nearest_nodes(graph, destinations.geometry.x, destinations.geometry.y)
    
    results = []
    
    for o_node in origin_nodes:
        dists = []
        for d_node in dest_nodes:
            try:
                # Calculate network distance in meters
                d = nx.shortest_path_length(graph, o_node, d_node, weight='length')
                dists.append(d)
            except nx.NetworkXNoPath:
                pass # Road not connected
        
        if dists:
            min_dist = min(dists) # Distance to NEAREST service
            time_min = min_dist / speed_mpm
            results.append(time_min)
        else:
            results.append(None)
            
    return results

# 4. RUN CALCULATIONS
# A. Hospitals (Driving)
wards['time_hospital'] = calculate_access_time(G, wards, hospitals, DRIVE_SPEED, "Hospitals")

# B. Schools (Walking)
wards['time_school'] = calculate_access_time(G, wards, schools, WALK_SPEED, "Schools")

# C. Transport (Walking)
wards['time_transport'] = calculate_access_time(G, wards, transport, WALK_SPEED, "Transport")

# 5. EXPORT RESULTS
print("3. Saving Results...")

# Save CSV for R Analysis (Stats)
# We select only the columns we need for the CSV
df_export = wards[['ward_id', 'time_hospital', 'time_school', 'time_transport']]
df_export.to_csv(OUTPUT_CSV, index=False)
print(f"   - CSV saved to: {OUTPUT_CSV}")

# --- FIX: DROP EXTRA GEOMETRY BEFORE SAVING ---
if 'centroid' in wards.columns:
    wards = wards.drop(columns=['centroid'])
# ----------------------------------------------

# Save GPKG for Map Visualization
wards.to_file(OUTPUT_GPKG, layer="wards_with_access", driver="GPKG")
print(f"   - Map Layer saved to: {OUTPUT_GPKG}")

print("✅ DONE! Network Analysis Complete.")