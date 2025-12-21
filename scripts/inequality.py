import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx

# --- CONFIGURATION ---
INPUT_GPKG = "vadodara_project_data.gpkg"
LAYER_NAME = "wards_final_index"
OUTPUT_IMAGE = "inequality_map.png"

print("--- GENERATING INEQUALITY MAP ---")

# 1. LOAD DATA
try:
    gdf = gpd.read_file(INPUT_GPKG, layer=LAYER_NAME)
except Exception as e:
    print(f"Error: Could not load layer. Make sure you ran '03_construct_index.py' first.\n{e}")
    exit()

# 2. SETUP THE PLOT
# Create a figure with high resolution (dpi=300)
fig, ax = plt.subplots(1, 1, figsize=(10, 10), dpi=300)

# 3. PLOT THE CHOROPLETH ( The "Green vs Red" logic)
# column='UOI_Score': The data we are mapping
# cmap='RdYlGn': Red (Low Score) to Green (High Score) color ramp
# scheme='NaturalBreaks': Smart clustering of data
# alpha=0.8: Slight transparency so we can see the basemap later
gdf.plot(column='UOI_Score', 
         cmap='RdYlGn', 
         linewidth=0.8, 
         ax=ax, 
         edgecolor='0.5', 
         legend=True,
         legend_kwds={'label': "Urban Opportunity Index (0-100)", 'shrink': 0.6},
         scheme='NaturalBreaks', k=5, alpha=0.8)

# 4. ADD LABELS (Ward Names)
# This loops through every ward and writes its name at the center
for idx, row in gdf.iterrows():
    # Only label if the ward is large enough to avoid clutter
    if row['geometry'].area > 0: 
        ax.annotate(text=row.get('ward_name', row.get('ward_id', '')), # Try name, fallback to ID
                    xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                    horizontalalignment='center',
                    fontsize=6,
                    color='black',
                    weight='bold')

# 5. ADD BASEMAP (Context)
# This downloads a background map from OpenStreetMap
try:
    ctx.add_basemap(ax, crs=gdf.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik, alpha=0.5)
except:
    print("Warning: Could not fetch basemap (internet issue?). Plotting without it.")

# 6. FORMATTING
ax.set_axis_off() # Remove the box/coordinates around the map
ax.set_title("Urban Inequality in Vadodara: Opportunity Index", fontsize=14, fontweight='bold')

# 7. SAVE
plt.tight_layout()
plt.savefig(OUTPUT_IMAGE)
print(f"🎉 Map saved as: {OUTPUT_IMAGE}")
print("Open this image to see which wards are Green (High Opportunity) and Red (Deprived).")