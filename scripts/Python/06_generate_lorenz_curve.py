import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# --- CONFIGURATION ---
MASTER_FILE = "data/processed/vadodara_final_index.gpkg"
ENV_FILE = "data/processed/ward_indicators.csv"  # To recover green_density
OUTPUT_DIR = "results/stats"


# --- CALCULATION FUNCTIONS ---
def gini(array):
    """Calculate the Gini coefficient."""
    array = np.array(array, dtype=np.float64)
    array = array.flatten()
    array = array[np.isfinite(array)]  # Remove NaNs
    if len(array) == 0:
        return 0.0
    if np.amin(array) < 0:
        array -= np.amin(array)

    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return (np.sum((2 * index - n - 1) * array)) / (n * np.sum(array))


def plot_lorenz_curve(df, column, title, filename, invert=False):
    # Check if column exists
    if column not in df.columns:
        print(f"⚠️  Skipping {title}: Column '{column}' not found.")
        return None

    values = df[column].dropna().values

    # Invert logic for "Bad" things (Travel Time) to measure "Good" (Access)
    if invert:
        # Avoid division by zero
        values = 1 / (values + 0.1)
        title = f"{title} (Inequality of Access)"

    values.sort()

    # Cumulative sums
    cum_values = np.cumsum(values) / np.sum(values)
    cum_population = np.linspace(0, 1, len(values))

    # Insert 0,0 start point
    cum_values = np.insert(cum_values, 0, 0)
    cum_population = np.insert(cum_population, 0, 0)

    # Calculate Gini
    gini_score = gini(values)

    # Plot
    plt.figure(figsize=(8, 8))
    plt.plot(
        cum_population,
        cum_values,
        label=f"Gini Coefficient = {gini_score:.2f}",
        linewidth=2,
        color="purple",
    )
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect Equality")
    plt.fill_between(
        cum_population, cum_population, cum_values, color="purple", alpha=0.1
    )

    plt.title(f"Lorenz Curve: {title}", fontsize=14, weight="bold")
    plt.xlabel("Cumulative % of Wards (Sorted Poor to Rich)", fontsize=12)
    plt.ylabel("Cumulative Share of Resource", fontsize=12)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)

    output_path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(output_path, dpi=300)
    print(f"✅ Saved Chart: {output_path} (Gini: {gini_score:.2f})")
    plt.close()
    return gini_score


# --- MAIN EXECUTION ---
print("--- CALCULATING INEQUALITY METRICS ---")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Load Master File
if not os.path.exists(MASTER_FILE):
    print(f"❌ Error: Master file {MASTER_FILE} not found.")
    sys.exit(1)

df_master = gpd.read_file(MASTER_FILE)
print(f"-> Loaded Master File ({len(df_master)} rows)")

# 2. Load Environmental Data (to get green_density back)
if os.path.exists(ENV_FILE):
    df_env = pd.read_csv(ENV_FILE)
    # Merge only if green_density isn't already there
    if "green_density" not in df_master.columns and "green_density" in df_env.columns:
        print("-> Merging Environmental Data to recover Green Density...")
        df_master = df_master.merge(
            df_env[["ward_id", "green_density"]], on="ward_id", how="left"
        )
else:
    print(f"⚠️ Warning: {ENV_FILE} not found. Green Space analysis might fail.")

# 3. Run Analysis
# We use 'time_hospital' because that is what your file log showed
g_green = plot_lorenz_curve(
    df_master, "green_density", "Green Space", "lorenz_greenery.png"
)
g_hosp = plot_lorenz_curve(
    df_master, "time_hospital", "Medical Access", "lorenz_medical.png", invert=True
)

print("\n" + "=" * 40)
print("FINAL THESIS STATISTICS (GINI COEFFICIENT)")
print("=" * 40)
if g_green is not None:
    print(f"Green Space Gini:   {g_green:.3f} (High Inequality if > 0.4)")
if g_hosp is not None:
    print(f"Medical Access Gini:{g_hosp:.3f} (High Inequality if > 0.4)")
print("=" * 40)
