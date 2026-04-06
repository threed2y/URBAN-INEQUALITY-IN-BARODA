import geopandas as gpd
import matplotlib.pyplot as plt
import os

# 1. Path to your integrated results
FILE_PATH = "/home/ethan/Downloads/URBAN-INEQUALITY-IN-BARODA/data/processed/vadodara_final_uoi_balanced.gpkg"
LAYER_NAME = "gnn_bym2_results"

if not os.path.exists(FILE_PATH):
    print(f"Error: Could not find {FILE_PATH}. Run GNN.py first!")
else:
    # Load the specific results layer
    gdf = gpd.read_file(FILE_PATH, layer=LAYER_NAME)

    # 2. Set up the plotting canvas
    fig, axes = plt.subplots(1, 3, figsize=(22, 7))

    # 3. Plot Original UOI (The Ground Truth)
    gdf.plot(column="UOI_Score", ax=axes[0], legend=True, 
             legend_kwds={'label': "Opportunity Index", 'orientation': "horizontal"},
             cmap="viridis", edgecolor="black", linewidth=0.1)
    axes[0].set_title("1. Observed UOI Score\n(Original Data)", fontsize=14)
    axes[0].axis("off")

    # 4. Plot SWMM Flood Impact (The Physical Shock)
    # This helps explain WHY the GNN predicted what it did
    gdf.plot(column="swmm_flood_road_pct", ax=axes[1], legend=True, 
             legend_kwds={'label': "% Road Failure", 'orientation': "horizontal"},
             cmap="Reds", edgecolor="black", linewidth=0.1)
    axes[1].set_title("2. SWMM Hydraulic Impact\n(1,003 Road Failures)", fontsize=14, color="darkred")
    axes[1].axis("off")

    # 5. Plot Hybrid GNN+BYM2 Prediction (The Social Science Result)
    gdf.plot(column="hybrid_opportunity_score", ax=axes[2], legend=True, 
             legend_kwds={'label': "Predicted Opportunity", 'orientation': "horizontal"},
             cmap="viridis", edgecolor="black", linewidth=0.1)
    axes[2].set_title("3. GNN + BYM2 Prediction\n(Spatial Inequality Refined)", fontsize=14)
    axes[2].axis("off")

    plt.suptitle("Vadodara Urban Inequality: Hydraulic Risk vs. Opportunity", fontsize=18, y=0.95)
    plt.tight_layout()
    
    # Save the figure for your submission
    output_png = "vadodara_inequality_map.png"
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to: {output_png}")
    plt.show()