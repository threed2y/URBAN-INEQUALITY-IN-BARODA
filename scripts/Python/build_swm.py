import osmnx as ox
import pandas as pd
import numpy as np
import os

# CONFIGURATION
PLACE_NAME = "Vadodara, Gujarat, India"
INP_FILE = "vadodara_overland.inp"
STORM_PEAK = 0.08 # High intensity for GNN failure scenarios

print(f"--- Building SWMM Network for {PLACE_NAME} ---")

# 1. Load Major Network
cf = '["highway"~"primary|secondary|tertiary|trunk"]'
G = ox.graph_from_place(PLACE_NAME, network_type='drive', custom_filter=cf, simplify=True)
G_proj = ox.project_graph(G, to_crs="EPSG:32643")
nodes, edges = ox.graph_to_gdfs(G_proj)

# 2. Synthetic Elevations (South-East Slope)
rng = np.random.default_rng(42)
cx, cy = nodes.geometry.x.mean(), nodes.geometry.y.mean()
nodes['elevation'] = (35.0 - (nodes.geometry.y - cy)/1000*0.5 - (nodes.geometry.x - cx)/1000*0.3 + rng.normal(0,0.05,len(nodes)))

# 3. Identify Outfalls (5 lowest nodes)
outfall_candidates = nodes.nsmallest(5, 'elevation')

with open(INP_FILE, 'w') as f:
    f.write("[TITLE]\nVadodara Robust Flood Model\n\n")
    f.write("[OPTIONS]\nFLOW_UNITS CMS\nINFILTRATION HORTON\nFLOW_ROUTING DYNWAVE\nSTART_DATE 01/01/2026\nSTART_TIME 00:00:00\nEND_DATE 01/01/2026\nEND_TIME 04:00:00\nREPORT_STEP 00:05:00\nROUTING_STEP 00:00:05\nALLOW_PONDING YES\n\n")

    f.write("[JUNCTIONS]\n")
    for nid, row in nodes.iterrows():
        # STABILITY FIX: Aponded=1000 prevents 'Instant Surcharge' crashes at 0.02 CMS
        f.write(f"{nid:<22} {row['elevation']:<10.3f} 2.0  0  0.5  1000\n")

    f.write("\n[OUTFALLS]\n")
    for i, (nid, row) in enumerate(outfall_candidates.iterrows()):
        f.write(f"OUTFALL_{i:<15} {row['elevation']-1.5:<10.3f} FREE NO\n")

    f.write("\n[CONDUITS]\n")
    for idx, row in edges.iterrows():
        u, v, key = idx
        f.write(f"R_{u}_{v}_{key:<15} {u:<20} {v:<20} {row['length']:<8.2f} 0.016 0 0\n")
    for i, (nid, _) in enumerate(outfall_candidates.iterrows()):
        f.write(f"DRAIN_{i:<16} {nid:<20} OUTFALL_{i:<19} 50.0 0.016 0 0\n")

    f.write("\n[XSECTIONS]\n")
    for idx, row in edges.iterrows():
        f.write(f"R_{idx[0]}_{idx[1]}_{idx[2]:<15} RECT_OPEN 2.0 5.0 0 0 1\n")
    for i in range(len(outfall_candidates)):
        f.write(f"DRAIN_{i:<16} RECT_OPEN 5.0 20.0 0 0 1\n")

    f.write("\n[TIMESERIES]\n")
    # STABILITY FIX: Gradual ramp-up (15m to 60m)
    f.write(f"STORM 0:00 0.0\nSTORM 0:15 {STORM_PEAK*0.2}\nSTORM 1:00 {STORM_PEAK}\nSTORM 2:00 {STORM_PEAK*0.5}\nSTORM 4:00 0.0\n")

    f.write("\n[INFLOWS]\n")
    for nid in nodes.index:
        f.write(f"{nid:<22} FLOW STORM FLOW 1.0 1.0\n")

    f.write("\n[REPORT]\nINPUT NO\nCONTROLS NO\nNODES ALL\nLINKS ALL\n")

print(f"Network built: {len(nodes)} nodes, {len(edges)} roads.")