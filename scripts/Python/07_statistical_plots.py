import geopandas as gpd
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import scipy.stats as stats
import os
import numpy as np

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(BASE_DIR, "data", "processed", "vadodara_final_uoi.gpkg")
OUTPUT_DIR = os.path.join(BASE_DIR, "results", "figures")


def generate_plots():
    print("--- STEP 7: GENERATING STATISTICAL PLOTS ---")

    if not os.path.exists(INPUT_GPKG):
        print("❌ Error: Run Step 5 first.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load Data
    gdf = gpd.read_file(INPUT_GPKG)

    # Create a clean DataFrame for plotting (drop geometry)
    df = pd.DataFrame(gdf.drop(columns="geometry"))

    # Set Theme
    sns.set_theme(style="whitegrid")

    # ==========================================
    # PLOT A: CORRELATION HEATMAP
    # ==========================================
    print("-> Generating Correlation Matrix...")
    cols = [
        "UOI_Score",
        "Score_Health",
        "Score_Edu",
        "Score_Mobility",
        "flood_risk_pct",
    ]
    corr = df[cols].corr()

    plt.figure(figsize=(10, 8))
    heatmap = sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1, fmt=".2f")
    plt.title("Correlation Matrix: Opportunity vs Risk", fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "01_correlation_matrix.png"), dpi=300)
    plt.close()

    # ==========================================
    # PLOT B: "THE TRAP" (SCATTER PLOT)
    # Flood Risk vs UOI Score
    # ==========================================
    print("-> Generating 'Inequality Trap' Scatter Plot...")

    plt.figure(figsize=(10, 6))
    sns.regplot(
        x="flood_risk_pct",
        y="UOI_Score",
        data=df,
        scatter_kws={"alpha": 0.6, "color": "#d73027"},
        line_kws={"color": "#4575b4"},
    )

    # Calculate Correlation
    r, p = stats.pearsonr(df["flood_risk_pct"], df["UOI_Score"])

    plt.title(
        f"The Vulnerability Trap: Flood Risk vs Opportunity\n(Pearson r={r:.2f}, p={p:.4f})",
        fontsize=14,
    )
    plt.xlabel("Flood Risk (% Area Submerged)", fontsize=12)
    plt.ylabel("Urban Opportunity Index (UOI)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.7)

    plt.savefig(os.path.join(OUTPUT_DIR, "02_scatter_flood_vs_uoi.png"), dpi=300)
    plt.close()

    # ==========================================
    # PLOT C: DISTRIBUTION OF OPPORTUNITY
    # ==========================================
    print("-> Generating Distribution Histogram...")

    plt.figure(figsize=(10, 6))
    sns.histplot(df["UOI_Score"], kde=True, bins=10, color="#4575b4", edgecolor="black")

    # Add vertical line for mean
    plt.axvline(
        df["UOI_Score"].mean(),
        color="red",
        linestyle="dashed",
        linewidth=2,
        label=f"Mean: {df['UOI_Score'].mean():.1f}",
    )

    plt.title("Distribution of Opportunity in Vadodara", fontsize=14)
    plt.xlabel("UOI Score (0-100)", fontsize=12)
    plt.legend()

    plt.savefig(os.path.join(OUTPUT_DIR, "03_uoi_distribution.png"), dpi=300)
    plt.close()

    print(f"✅ Plots saved to: {OUTPUT_DIR}")
    print(f"   -> Correlation Coefficient (Flood vs UOI): {r:.2f}")
    if r < -0.3:
        print(
            "   ✅ INSIGHT: Significant Negative Correlation found! (Higher Flood Risk = Lower Opportunity)"
        )


if __name__ == "__main__":
    generate_plots()
