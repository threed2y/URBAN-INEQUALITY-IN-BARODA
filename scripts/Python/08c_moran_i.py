import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from libpysal.weights import KNN
from esda.moran import Moran, Moran_Local
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UOI_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)

OUT_DIR = os.path.join(BASE_DIR, "results", "spatial_diagnostics")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_SCATTER = os.path.join(OUT_DIR, "Figure_Moran_Scatter_LISA.png")
OUT_LISA = os.path.join(OUT_DIR, "Figure_LISA_Clusters.png")

# --------------------------------------------------
# COLOR SCHEME (LOCKED)
# --------------------------------------------------
COLORS = {
    "High-High": "#b2182b",  # red
    "Low-Low": "#2166ac",  # blue
    "High-Low": "#ef8a62",  # orange
    "Low-High": "#8073ac",  # purple
    "Not Significant": "#d9d9d9",
}

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
gdf = gpd.read_file(UOI_GPKG)

# Spatial weights
w = KNN.from_dataframe(gdf, k=4)
w.transform = "r"

y = gdf["UOI_Score"].values

# Moran
moran = Moran(y, w, permutations=9999)
local = Moran_Local(y, w, permutations=9999)


# --------------------------------------------------
# ASSIGN LISA LABELS
# --------------------------------------------------
def lisa_label(q, p):
    if p > 0.05:
        return "Not Significant"
    return {
        1: "High-High",
        2: "Low-High",
        3: "Low-Low",
        4: "High-Low",
    }[q]


gdf["lisa_cluster"] = [lisa_label(local.q[i], local.p_sim[i]) for i in range(len(gdf))]

# Spatial lag for scatter plot
gdf["spatial_lag"] = w.sparse @ y

# FIX I-13: standard Moran scatter requires DEMEANED axes.
# Plotting raw UOI_Score shifts the quadrant boundaries, mislabelling
# which wards fall in HH / LL / HL / LH quadrants.
y_mean   = gdf["UOI_Score"].mean()
lag_mean = gdf["spatial_lag"].mean()
gdf["uoi_demeaned"] = gdf["UOI_Score"] - y_mean
gdf["lag_demeaned"] = gdf["spatial_lag"] - lag_mean

# --------------------------------------------------
# 1. MORAN SCATTER PLOT (COLORED BY LISA)
# --------------------------------------------------
plt.figure(figsize=(7, 7))

for cluster, color in COLORS.items():
    sub = gdf[gdf["lisa_cluster"] == cluster]
    plt.scatter(
        sub["uoi_demeaned"],
        sub["lag_demeaned"],
        label=cluster,
        color=color,
        edgecolor="black",
        s=80,
        alpha=0.85,
    )

# Quadrant dividers at 0 are correct once both axes are demeaned
plt.axhline(0, color="black", linestyle="--", linewidth=1)
plt.axvline(0, color="black", linestyle="--", linewidth=1)

plt.xlabel("UOI Score (demeaned)")
plt.ylabel("Spatial Lag of UOI (demeaned)")
plt.title(f"Moran's I Scatter Plot (I = {moran.I:.3f}, p = {moran.p_sim:.3f})")

plt.legend(frameon=False)
plt.tight_layout()
plt.savefig(OUT_SCATTER, dpi=300)
plt.close()

# --------------------------------------------------
# 2. LISA CLUSTER MAP
# --------------------------------------------------
fig, ax = plt.subplots(1, 1, figsize=(8, 8))

for cluster, color in COLORS.items():
    gdf[gdf["lisa_cluster"] == cluster].plot(
        ax=ax,
        color=color,
        edgecolor="black",
        linewidth=0.4,
        label=cluster,
    )

ax.set_title("Local Spatial Clusters of Urban Opportunity (LISA)", fontsize=14)
ax.axis("off")
ax.legend(frameon=False, loc="lower left")

plt.tight_layout()
plt.savefig(OUT_LISA, dpi=300)
plt.close()

print("✅ Moran–LISA linked diagnostics generated")
print(f" → {OUT_SCATTER}")
print(f" → {OUT_LISA}")
