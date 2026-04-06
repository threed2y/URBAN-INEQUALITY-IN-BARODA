import os
import re
import pandas as pd
import geopandas as gpd
import osmnx as ox
from pyswmm import Simulation, Output
from swmm.toolkit.shared_enum import LinkAttribute

# PATH SETUP
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
INP_FILE = os.path.join(SCRIPT_DIR, "vadodara_overland.inp")
OUT_FILE = os.path.join(SCRIPT_DIR, "vadodara_overland.out")
WARDS_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "vadodara_final_uoi_balanced.gpkg")
OUTPUT_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "swmm_road_failures.csv")

# 1. RUN SIMULATION
print(f"--- Starting Simulation: {INP_FILE} ---")
with Simulation(INP_FILE) as sim:
    for step in sim: pass
print("Simulation Complete.")

# 2. BINARY EXTRACTION
parsed_rows = []
E_RE = re.compile(r'^R_(\d+)_(\d+)_(\d+)$')

with Output(OUT_FILE) as out:
    all_links = list(out.links.keys())
    print(f"Extracted {len(all_link_ids := all_links)} links from binary.")
    for lid in all_link_ids:
        m = E_RE.match(lid)
        if m:
            series = out.link_series(lid, LinkAttribute.FLOW_DEPTH)
            depths = list(series.values())
            max_d = max(depths) if depths else 0.0
            parsed_rows.append({'u':int(m.group(1)), 'v':int(m.group(2)), 'key':int(m.group(3)), 'max_depth':max_d})

df = pd.DataFrame(parsed_rows)
df['is_flooded'] = (df['max_depth'] > 0.30).astype(int)
df.to_csv(OUTPUT_CSV, index=False)
print(f"Road Failures Saved: {len(df)} roads. Failures: {df['is_flooded'].sum()}")

# 3. WARD AGGREGATION
if os.path.exists(WARDS_FILE):
    print("Aggregating to Wards...")
    cf = '["highway"~"primary|secondary|tertiary|trunk"]'
    G = ox.graph_from_place("Vadodara, Gujarat, India", network_type='drive', custom_filter=cf, simplify=True)
    _, edges_geom = ox.graph_to_gdfs(G)
    edges_geom = edges_geom.reset_index().merge(df, on=['u','v','key'], how='inner')
    
    wards = gpd.read_file(WARDS_FILE).to_crs("EPSG:32643")
    edges_proj = edges_geom.to_crs("EPSG:32643")
    edges_proj['len'] = edges_proj.geometry.length
    
    joined = gpd.sjoin(edges_proj, wards, how='inner', predicate='intersects')
    stats = joined.groupby('index_right').apply(lambda x: pd.Series({
        'swmm_flood_road_pct': (x.loc[x['is_flooded']==1,'len'].sum() / x['len'].sum()) * 100,
        'swmm_mean_depth': x['max_depth'].mean()
    }))
    cols_to_drop = ['swmm_flood_road_pct', 'swmm_mean_depth']
    wards = wards.drop(columns=[c for c in cols_to_drop if c in wards.columns])
    
    wards = wards.join(stats).fillna(0)
    wards.to_file(WARDS_FILE, driver="GPKG")
    print(f"Final Ward Data saved to: {WARDS_FILE}")