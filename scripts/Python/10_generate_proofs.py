import geopandas as gpd
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np
import os
from libpysal.weights import KNN
from esda.moran import Moran, Moran_Local
from splot.esda import lisa_cluster, plot_moran

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(BASE_DIR, "data", "processed", "vadodara_final_uoi.gpkg")
OUTPUT_DIR = os.path.join(BASE_DIR, "results", "thesis_proofs")


def generate_proofs():
    print("--- STEP 10: GENERATING THESIS PROOFS (VISUAL EVIDENCE) ---")

    if not os.path.exists(INPUT_GPKG):
        print("❌ Error: Run Step 5 first.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load Data
    gdf = gpd.read_file(INPUT_GPKG)
    df = pd.DataFrame(gdf.drop(columns="geometry"))

    # Set Academic Theme
    sns.set_theme(style="whitegrid", font_scale=1.2)

    # ==========================================
    # PROOF 1: THE VULNERABILITY TRAP (Regression)
    # Evidence: "Do flood-prone areas have less opportunity?"
    # ==========================================
    print("-> Generating Proof 1: The Vulnerability Trap...")
    plt.figure(figsize=(10, 7))
    sns.regplot(
        x="flood_risk_pct",
        y="UOI_Score",
        data=df,
        scatter_kws={"alpha": 0.6, "color": "#d73027", "s": 100},
        line_kws={"color": "#4575b4", "linewidth": 3},
    )

    r, p = stats.pearsonr(df["flood_risk_pct"], df["UOI_Score"])
    plt.title(
        f"PROOF 1: The Vulnerability Trap\n(Pearson r={r:.2f}, p={p:.4f})",
        fontweight="bold",
    )
    plt.xlabel("Flood Risk (% Area Submerged)")
    plt.ylabel("Urban Opportunity Index (UOI)")
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_01_Vulnerability_Trap.png"), dpi=300)
    plt.close()

    # ==========================================
    # PROOF 2: THE PRIVILEGE GAP (Distribution)
    # Evidence: "Is the city equal, or is it divided?"
    # ==========================================
    print("-> Generating Proof 2: Opportunity Distribution...")
    plt.figure(figsize=(10, 6))
    sns.histplot(df["UOI_Score"], kde=True, bins=15, color="#4575b4", edgecolor="black")
    plt.axvline(
        df["UOI_Score"].mean(),
        color="red",
        linestyle="--",
        label=f"Mean: {df['UOI_Score'].mean():.1f}",
    )
    plt.title(
        "PROOF 2: Distribution of Opportunity (The Privilege Gap)", fontweight="bold"
    )
    plt.xlabel("UOI Score")
    plt.legend()
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_02_Distribution.png"), dpi=300)
    plt.close()

    # ==========================================
    # PROOF 3: THE LORENZ CURVE (Inequality)
    # Evidence: "Visualizing the Gini Coefficient"
    # ==========================================
    print("-> Generating Proof 3: Lorenz Curve (Inequality)...")

    # Calculate Lorenz Curve
    X = df["UOI_Score"].values
    X = np.sort(X)
    # Cumulative sum of population (x-axis) vs Cumulative sum of wealth/score (y-axis)
    n = len(X)
    lorenz_curve = np.cumsum(X) / X.sum()
    perfect_equality = np.linspace(0, 1, n)

    plt.figure(figsize=(8, 8))
    plt.plot(
        np.linspace(0, 1, n),
        lorenz_curve,
        color="#d73027",
        linewidth=3,
        label="Vadodara (Actual)",
    )
    plt.plot([0, 1], [0, 1], color="black", linestyle="--", label="Perfect Equality")
    plt.fill_between(
        np.linspace(0, 1, n), perfect_equality, lorenz_curve, color="#d73027", alpha=0.1
    )

    plt.title("PROOF 3: Lorenz Curve of Urban Inequality", fontweight="bold")
    plt.xlabel("Cumulative Share of Wards (Poorest to Richest)")
    plt.ylabel("Cumulative Share of Opportunity")
    plt.legend()
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_03_Lorenz_Curve.png"), dpi=300)
    plt.close()

    # ==========================================
    # PROOF 4: SPATIAL CLUSTERING (Global Moran's I)
    # Evidence: "Is poverty random, or segregated?"
    # ==========================================
    print("-> Generating Proof 4: Spatial Segregation (Moran's I)...")

    w = KNN.from_dataframe(gdf, k=4)
    w.transform = "r"
    y = gdf["UOI_Score"].values
    moran = Moran(y, w)

    fig, ax = plot_moran(moran, zstandard=True, figsize=(10, 5))
    plt.suptitle(
        f"PROOF 4: Spatial Segregation Test (Moran's I = {moran.I:.2f})",
        fontweight="bold",
    )
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_04_Moran_Scatter.png"), dpi=300)
    plt.close()

    # ==========================================
    # PROOF 5: THE GHETTO MAP (LISA Clusters)
    # Evidence: "Where exactly are the trapped zones?"
    # ==========================================
    print("-> Generating Proof 5: The Segregation Map (LISA)...")

    m_local = Moran_Local(y, w)
    fig, ax = plt.subplots(figsize=(12, 10))
    lisa_cluster(m_local, gdf, p=0.05, ax=ax)
    plt.title(
        "PROOF 5: Structural Segregation Map\n(Red=Elite Enclaves, Blue=Deprived Clusters)",
        fontweight="bold",
    )
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_05_Segregation_Map.png"), dpi=300)
    plt.close()

    print(f"✅ All Proofs Generated in: {OUTPUT_DIR}")
    print("   1. Figure_01_Vulnerability_Trap.png  (Flood vs Opportunity)")
    print("   2. Figure_02_Distribution.png        (The Gap)")
    print("   3. Figure_03_Lorenz_Curve.png        (Visual Gini)")
    print("   4. Figure_04_Moran_Scatter.png       (Statistical Segregation)")
    print("   5. Figure_05_Segregation_Map.png     (Geographic Segregation)")


if __name__ == "__main__":
    generate_proofs()

python3 Python/10_generate_proofs.py
--- STEP 10: GENERATING THESIS PROOFS (VISUAL EVIDENCE) ---
-> Generating Proof 1: The Vulnerability Trap...
-> Generating Proof 2: Opportunity Distribution...
-> Generating Proof 3: Lorenz Curve (Inequality)...
-> Generating Proof 4: Spatial Segregation (Moran's I)...
-> Generating Proof 5: The Segregation Map (LISA)...
✅ All Proofs Generated in: /home/ethan/Downloads/URBAN-INEQUALITY-IN-BARODA/results/thesis_proofs
   1. Figure_01_Vulnerability_Trap.png  (Flood vs Opportunity)
   2. Figure_02_Distribution.png        (The Gap)
   3. Figure_03_Lorenz_Curve.png        (Visual Gini)                                                    4. Figure_04_Moran_Scatter.png       (Statistical Segregation)                                        5. Figure_05_Segregation_Map.png     (Geographic Segregation)
