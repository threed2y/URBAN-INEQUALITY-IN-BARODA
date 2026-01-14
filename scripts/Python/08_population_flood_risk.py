import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- CONFIGURATION: USE ABSOLUTE PATHS ---
# This ensures it works regardless of where you run the script from
BASE_DIR = os.path.expanduser("~/Downloads/URBAN-INEQUALITY-IN-BARODA")
FLOOD_FILE = os.path.join(BASE_DIR, "data/processed/ward_flood_risk.csv")
INDICATORS_FILE = os.path.join(BASE_DIR, "data/processed/ward_indicators.csv")
OUTPUT_DATA = os.path.join(BASE_DIR, "results/ward_flood_population_analysis.csv")
OUTPUT_MAP = os.path.join(BASE_DIR, "results/maps/flood_risk_matrix.png")


def analyze_population_risk():
    print("--- STEP 8: POPULATION VS. LAND FLOOD RISK ---")
    print(f"-> Looking for Flood Data at: {FLOOD_FILE}")

    # 1. Load Data
    if not os.path.exists(FLOOD_FILE):
        print(f"❌ Error: Flood file missing.")
        return
    if not os.path.exists(INDICATORS_FILE):
        print(f"❌ Error: Indicators file missing.")
        return

    df_flood = pd.read_csv(FLOOD_FILE)
    df_ind = pd.read_csv(INDICATORS_FILE)

    # Merge on ward_id
    df = pd.merge(df_flood, df_ind, on="ward_id")

    # 2. Normalize Metrics (0 to 1 Scale)
    df["norm_flood"] = df["flood_risk_score"]
    min_pop = df["building_density"].min()
    max_pop = df["building_density"].max()
    df["norm_pop"] = (df["building_density"] - min_pop) / (max_pop - min_pop)

    # 3. Classify Wards
    def classify(row):
        if row["norm_flood"] > 0.3 and row["norm_pop"] > 0.5:
            return "CRITICAL (High Pop + Flood)"
        elif row["norm_flood"] > 0.4:
            return "HIGH LAND LOSS (Low Pop)"
        elif row["norm_pop"] > 0.7:
            return "DENSE (Low Flood Risk)"
        else:
            return "SAFE / LOW RISK"

    df["Risk_Category"] = df.apply(classify, axis=1)

    # 4. Save
    os.makedirs(os.path.dirname(OUTPUT_DATA), exist_ok=True)
    df.to_csv(OUTPUT_DATA, index=False)
    print(f"✅ SUCCESS: Data saved to {OUTPUT_DATA}")

    # 5. Plot
    plt.figure(figsize=(10, 8))
    sns.scatterplot(
        data=df,
        x="flood_risk_score",
        y="building_density",
        hue="Risk_Category",
        style="Risk_Category",
        s=200,
        palette="viridis",
    )
    plt.title("Flood Vulnerability Matrix")
    plt.savefig(OUTPUT_MAP, dpi=300)
    print(f"✅ Map saved to {OUTPUT_MAP}")


if __name__ == "__main__":
    analyze_population_risk()
