import geopandas as gpd
import osmnx as ox
import networkx as nx
import pandas as pd
from shapely.geometry import Point

# --- CONFIGURATION ---
NETWORK_FILE = "vadodara_network_drive.graphml"
DATA_FILE = "vadodara_project_data.gpkg"
OUTPUT_FILE = "ward_accessibility_scores.csv"

# Speed assumptions (in km/h) to calculate Travel Time
SPEED_Walk = 4.5
SPEED_Drive = 30  # Average urban speed for Vadodara

print("--- STARTING ACCESSIBILITY ANALYSIS ---")

# 1. LOAD DATA
print("1. Loading Network and Layers...")
# Load the Graph (The smart network file)
G = ox.load_graphml(NETWORK_FILE)

# Load the Layers (The visual map file)
wards = gpd.read_file(DATA_FILE, layer="wards")
hospitals = gpd.read_file(DATA_FILE, layer="hospitals")
schools = gpd.read_file(DATA_FILE, layer="schools")
transport = gpd.read_file(DATA_FILE, layer="transport")

# 2. PREPARE ORIGINS (WARD CENTROIDS)
print("2. Calculating Ward Centroids...")
# We assume the "average person" lives in the center of the ward
wards['centroid'] = wards.geometry.centroid

# 3. DEFINE THE CALCULATOR FUNCTION
def calculate_nearest_distance(graph, origins_gdf, destinations_gdf, network_type="drive"):
    """
    Calculates the shortest network distance from every Ward Center 
    to the NEAREST service point in the destination list.
    """
    results = []
    
    # A. Snap Points to the Network Grid
    # Find the nearest street intersection (node) for every Ward Center
    origin_nodes = ox.nearest_nodes(graph, X=origins_gdf.centroid.x, Y=origins_gdf.centroid.y)
    
    # Find the nearest street intersection for every Service (Hospital/School)
    dest_nodes = ox.nearest_nodes(graph, X=destinations_gdf.geometry.x, Y=destinations_gdf.geometry.y)
    
    print(f"   - Analyzing {len(origin_nodes)} Wards vs {len(dest_nodes)} Destinations...")

    # B. Calculate Distance for Each Ward
    for i, o_node in enumerate(origin_nodes):
        # Calculate distance from this Ward Node to ALL Service Nodes
        # Then just keep the minimum (the nearest one)
        
        # nx.single_source_dijkstra_path_length is efficient for this
        # It calculates distance to all reachble nodes. We filter for our targets.
        dists = []
        for d_node in dest_nodes:
            try:
                # 'length' is the distance in meters stored in the graph edges
                d = nx.shortest_path_length(graph, source=o_node, target=d_node, weight='length')
                dists.append(d)
            except nx.NetworkXNoPath:
                pass # Road might be disconnected
        
        if dists:
            min_dist_meters = min(dists)
            results.append(min_dist_meters)
        else:
            results.append(None) # Should not happen if network is clean
            
    return results

# 4. RUN ANALYSIS FOR EACH SERVICE
print("3. Running Network Analysis (This may take a moment)...")

# A. Hospitals
print("   > Processing Hospitals...")
wards['dist_hospital_m'] = calculate_nearest_distance(G, wards, hospitals)

# B. Schools
print("   > Processing Schools...")
wards['dist_school_m'] = calculate_nearest_distance(G, wards, schools)

# C. Transport
print("   > Processing Transport Hubs...")
wards['dist_transport_m'] = calculate_nearest_distance(G, wards, transport)

# 5. CONVERT TO TRAVEL TIME (MINUTES)
# Formula: Time (min) = (Distance (km) / Speed (km/h)) * 60
print("4. Converting Distances to Travel Time...")

wards['time_hospital_min'] = (wards['dist_hospital_m'] / 1000 / SPEED_Drive) * 60
wards['time_school_min'] = (wards['dist_school_m'] / 1000 / SPEED_Drive) * 60
wards['time_transport_min'] = (wards['dist_transport_m'] / 1000 / SPEED_Walk) * 60 # Assume walking to bus

# 6. SAVE RESULTS
# We save just the data table (CSV) for statistics
final_df = wards[['dist_hospital_m', 'time_hospital_min', 
                  'dist_school_m', 'time_school_min', 
                  'dist_transport_m', 'time_transport_min']]

# Save as CSV (for PCA analysis later)
final_df.to_csv(OUTPUT_FILE, index=True)

# FIX: Drop the temporary 'centroid' column before saving to GeoPackage
if 'centroid' in wards.columns:
    wards = wards.drop(columns=['centroid'])

# Save as Map Layer
print(f"Saving layer to {DATA_FILE}...")
wards.to_file(DATA_FILE, layer="wards_with_scores", driver="GPKG")

print(f"🎉 DONE! Results saved to:\n  1. {OUTPUT_FILE} (For Excel/Statistics)\n  2. {DATA_FILE} (Layer: 'wards_with_scores')")