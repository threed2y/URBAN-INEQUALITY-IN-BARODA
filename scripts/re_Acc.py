import geopandas as gpd
import osmnx as ox
import networkx as nx
import pandas as pd

# --- CONFIGURATION ---
NETWORK_FILE = "vadodara_network_drive.graphml" # Must be the graph you downloaded
DATA_FILE = "vadodara_project_data.gpkg"
OUTPUT_FILE = "ward_accessibility_scores_realistic.csv"

# --- "HUMANE" SPEED ASSUMPTIONS (km/h) ---
# We define speeds based on the type of road (OSM 'highway' tag)
speed_config = {
    'motorway': 60,
    'trunk': 50,
    'primary': 40,
    'secondary': 35,
    'tertiary': 30,
    'residential': 15,  # Much slower in neighborhoods
    'living_street': 10,
    'service': 10,
    'unclassified': 20,
    'default': 20
}

# TRAFFIC FACTOR: Reduce theoretical speed to account for signals/traffic
# 1.0 = Empty streets at 3 AM. 
# 0.7 = Normal day traffic (30% delay).
TRAFFIC_PENALTY = 0.7 

WALK_SPEED = 4.5 # km/h (Average human walking speed)

print("--- STARTING REALISTIC ANALYSIS ---")

# 1. LOAD DATA
print("1. Loading Data...")
# Load the Graph we saved earlier
G = ox.load_graphml(NETWORK_FILE)

# Load Layers (Using the corrected 12-ward file you have)
wards = gpd.read_file(DATA_FILE, layer="wards")
if 'centroid' in wards.columns: wards = wards.drop(columns=['centroid']) # Cleanup
wards['centroid'] = wards.geometry.centroid

# Load Services
hospitals = gpd.read_file(DATA_FILE, layer="hospitals")
schools = gpd.read_file(DATA_FILE, layer="schools")
transport = gpd.read_file(DATA_FILE, layer="transport")


# 2. ENRICH NETWORK WITH "REALISTIC" SPEEDS
print("2. Applying Road-Specific Speeds...")

# Helper function to assign speed based on road type
def get_speed(highway_tag):
    if isinstance(highway_tag, list): 
        highway_tag = highway_tag[0] # Handle cases where road has multiple tags
    return speed_config.get(highway_tag, speed_config['default'])

# Iterate through every street segment and assign travel time
for u, v, k, data in G.edges(keys=True, data=True):
    # A. Determine Max Speed
    if 'maxspeed' in data:
        # If OSM has a limit, use it (cleaning string to int)
        try:
            speed = float(str(data['maxspeed']).split()[0])
        except:
            speed = get_speed(data.get('highway'))
    else:
        # Fallback to our config
        speed = get_speed(data.get('highway'))
    
    # B. Apply Traffic Penalty (The "Reality Check")
    real_speed = speed * TRAFFIC_PENALTY
    
    # C. Calculate Time (Seconds) = Distance (meters) / Speed (m/s)
    dist_m = data['length']
    speed_mps = real_speed * (1000 / 3600) # Convert km/h to m/s
    
    data['drive_time_sec'] = dist_m / speed_mps
    
    # D. Calculate Walk Time (for Bus/Schools)
    # Walk speed is constant, unaffected by traffic jams
    walk_speed_mps = WALK_SPEED * (1000 / 3600)
    data['walk_time_sec'] = dist_m / walk_speed_mps


# 3. DEFINE CALCULATOR (WEIGHTED)
def calculate_travel_time(graph, origins_gdf, destinations_gdf, weight_col):
    """
    Calculates time using the specific weight column (drive_time or walk_time).
    """
    results = []
    
    # Snap points to network
    origin_nodes = ox.nearest_nodes(graph, X=origins_gdf.centroid.x, Y=origins_gdf.centroid.y)
    dest_nodes = ox.nearest_nodes(graph, X=destinations_gdf.geometry.x, Y=destinations_gdf.geometry.y)
    
    print(f"   - Routing {len(origin_nodes)} origins to {len(dest_nodes)} destinations...")

    for o_node in origin_nodes:
        times = []
        for d_node in dest_nodes:
            try:
                # Dijkstra using TIME as weight, not distance
                t = nx.shortest_path_length(graph, source=o_node, target=d_node, weight=weight_col)
                times.append(t)
            except nx.NetworkXNoPath:
                pass 
        
        if times:
            min_time_sec = min(times)
            results.append(min_time_sec / 60) # Convert seconds to Minutes
        else:
            results.append(None)
            
    return results

# 4. RUN ANALYSIS
print("3. Calculating Drive Times (Hospitals)...")
# We assume people drive to hospitals
wards['time_hospital_min'] = calculate_travel_time(G, wards, hospitals, weight_col='drive_time_sec')

print("4. Calculating Walk Times (Schools & Transport)...")
# We assume students/commuters walk (reflects inequality better - not everyone has a car)
wards['time_school_min'] = calculate_travel_time(G, wards, schools, weight_col='walk_time_sec')
wards['time_transport_min'] = calculate_travel_time(G, wards, transport, weight_col='walk_time_sec')


# 5. SAVE
# Clean up columns before saving
final_df = wards[['time_hospital_min', 'time_school_min', 'time_transport_min']]
final_df.to_csv(OUTPUT_FILE, index=True)

if 'centroid' in wards.columns: wards = wards.drop(columns=['centroid'])
wards.to_file(DATA_FILE, layer="wards_realistic_scores", driver="GPKG")

print(f"🎉 DONE! 'Humane' scores saved to {OUTPUT_FILE}")