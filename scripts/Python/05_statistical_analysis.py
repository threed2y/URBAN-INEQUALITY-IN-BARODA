import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import geopandas as gpd
import os

# --- CONFIGURATION ---
DATA_FILE = "results/ward_identities.csv"  # If you ran the naming script
# Fallback if naming script wasn't run yet:
if not os.path.exists(DATA_FILE):
    DATA_FILE = (
        "~/Downloads/URBAN-INEQUALITY-IN-BARODA/data/processed/ward_indicators.csv"
    )
    TRAVEL_FILE = (
        "~/Downloads/URBAN-INEQUALITY-IN-BARODA/data/processed/ward_travel_times.csv"
    )
    # Merge them manually if needed
    df1 = pd.read_csv(DATA_FILE)
    df2 = pd.read_csv(TRAVEL_FILE)
    df = pd.merge(df1, df2, on="ward_id")
else:
    df = pd.read_csv(DATA_FILE)

# Add "Distance from Center" (We need to calculate this from the map)
wards = gpd.read_file(
    "~/Downloads/URBAN-INEQUALITY-IN-BARODA/data/interim/vadodara_project.gpkg"
)
# Calculate centroid distance from Ward 1 (assuming Ward 1 is center) or the geometric center
# Let's use the explicit city center coordinate we used before
from shapely.geometry import Point

city_center = gpd.GeoSeries(
    [Point(312574, 2467770)], crs="EPSG:32643"
)  # Approx UTM center
wards["dist_to_center_km"] = (
    wards.geometry.centroid.distance(city_center.iloc[0]) / 1000
)

# Merge distance back to main data
df = df.merge(wards[["ward_id", "dist_to_center_km"]], on="ward_id")

# --- 1. PREPARE DATA FOR CORRELATION ---
# We want to correlate:
# - Distance from Center (Independent Variable)
# - Green Density
# - Building Density
# - Hospital Time
# - Transport Time
# - Urban Score

cols_to_analyze = [
    "dist_to_center_km",
    "green_density",
    "building_density",
    "hospitals_min",
    "schools_min",
    "transport_min",
]

# Rename for cleaner charts
clean_names = {
    "dist_to_center_km": "Dist to Center (km)",
    "green_density": "Greenery (%)",
    "building_density": "Built Density (%)",
    "hospitals_min": "Time to Hospital",
    "schools_min": "Time to School",
    "transport_min": "Time to Transport",
}

corr_df = df[cols_to_analyze].rename(columns=clean_names)

# --- 2. GENERATE CORRELATION MATRIX ---
plt.figure(figsize=(10, 8))
corr_matrix = corr_df.corr()

# Plot Heatmap
sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
plt.title(
    "Correlation Matrix: Urban Indicators in Vadodara", fontsize=16, weight="bold"
)

# Save
os.makedirs("results/stats", exist_ok=True)
plt.savefig("results/stats/correlation_matrix.png", dpi=300, bbox_inches="tight")
print("✅ Generated Correlation Matrix -> results/stats/correlation_matrix.png")

# --- 3. GENERATE SUMMARY TABLE ---
summary = corr_df.describe().T[["mean", "std", "min", "50%", "max"]]
summary.columns = ["Mean", "Std Dev", "Min", "Median", "Max"]
summary.to_csv("results/stats/descriptive_statistics.csv")
print("✅ Generated Stats Table -> results/stats/descriptive_statistics.csv")

# Print Key Findings
print("\n--- KEY STATISTICAL FINDINGS ---")
print(f"Average Time to Hospital: {summary.loc['Time to Hospital', 'Mean']:.2f} mins")
print(f"Max Time to Hospital:     {summary.loc['Time to Hospital', 'Max']:.2f} mins")

# Check Correlation: Distance vs Hospital
r_dist_hosp = corr_matrix.loc["Dist to Center (km)", "Time to Hospital"]
print(f"\nCorrelation (Distance vs Hospital Access): r = {r_dist_hosp:.2f}")
if r_dist_hosp > 0.5:
    print(
        "-> CONCLUSION: Strong Positive Correlation. As you move away from the center, access significantly worsens."
    )
elif r_dist_hosp > 0.3:
    print(
        "-> CONCLUSION: Moderate Correlation. Peripheral areas have somewhat worse access."
    )
else:
    print("-> CONCLUSION: No significant spatial bias found.")
