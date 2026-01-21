import geopandas as gpd
import pandas as pd
import numpy as np
import os
from scipy.stats import pearsonr, linregress

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# This must match the output from Step 5
INPUT_GPKG = os.path.join(BASE_DIR, "data", "processed", "vadodara_final_uoi.gpkg")
OUTPUT_REPORT = os.path.join(BASE_DIR, "results", "FINAL_THESIS_RESULTS.txt")
OUTPUT_CSV = os.path.join(BASE_DIR, "results", "ward_rankings.csv")


def gini(array):
    """Calculate the Gini coefficient of a numpy array."""
    # Standard Gini formula
    array = array.flatten()
    if np.amin(array) < 0:
        array -= np.amin(array)
    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return (np.sum((2 * index - n - 1) * array)) / (n * np.sum(array))


def compile_results():
    print("--- STEP 9: COMPILING FINAL THESIS RESULTS (FIXED) ---")

    # 1. Verification
    if not os.path.exists(INPUT_GPKG):
        print(f"❌ Error: Input file not found:\n   {INPUT_GPKG}")
        print("👉 Solution: Run 'python3 scripts/python/05_calculate_uoi.py' first.")
        return

    # 2. Load Data
    print(f"-> Loading Data from {os.path.basename(INPUT_GPKG)}...")
    gdf = gpd.read_file(INPUT_GPKG)
    df = pd.DataFrame(gdf.drop(columns="geometry"))

    # 3. Generate Report
    print("-> Calculating Statistics...")
    with open(OUTPUT_REPORT, "w") as f:
        f.write("==================================================\n")
        f.write("       URBAN INEQUALITY IN VADODARA: RESULTS      \n")
        f.write("==================================================\n\n")

        # --- SECTION A: DESCRIPTIVE STATISTICS ---
        f.write("1. CITY-WIDE OVERVIEW\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total Wards Analyzed: {len(df)}\n")
        f.write(
            f"Average Opportunity Score (UOI): {df['UOI_Score'].mean():.2f} / 100\n"
        )
        f.write(f"Average Flood Risk: {df['flood_risk_pct'].mean():.2f}%\n")
        f.write(
            f"Average Hospital Access Time: {df['hospitals_min'].mean():.1f} mins\n"
        )
        f.write(
            f"Average School Access Time:   {df['schools_min'].mean():.1f} mins\n\n"
        )

        # --- SECTION B: INEQUALITY METRICS ---
        f.write("2. INEQUALITY METRICS\n")
        f.write("-" * 30 + "\n")

        # Gini Coefficient
        gini_score = gini(df["UOI_Score"].values)
        f.write(f"Gini Coefficient (Opportunity): {gini_score:.3f}\n")
        if gini_score > 0.4:
            f.write("   -> INTERPRETATION: High Inequality (Severe Structural Gaps)\n")
        elif gini_score > 0.3:
            f.write("   -> INTERPRETATION: Moderate Inequality\n")
        else:
            f.write("   -> INTERPRETATION: Low Inequality\n")

        # The "Gap" (Top 10% vs Bottom 10%)
        top_10 = df["UOI_Score"].quantile(0.90)
        bot_10 = df["UOI_Score"].quantile(0.10)
        gap_ratio = top_10 / bot_10 if bot_10 > 0 else 0
        f.write(f"The 'Privilege Gap' (Top 10% vs Bottom 10%): {gap_ratio:.1f}x\n")
        f.write(
            f"   (Residents in top wards have {gap_ratio:.1f} times more opportunity than bottom wards.)\n\n"
        )

        # --- SECTION C: THE VULNERABILITY TRAP ---
        f.write("3. THE VULNERABILITY TRAP (CORRELATION)\n")
        f.write("-" * 30 + "\n")
        r, p = pearsonr(df["flood_risk_pct"], df["UOI_Score"])
        slope, intercept, r_value, p_value, std_err = linregress(
            df["flood_risk_pct"], df["UOI_Score"]
        )

        f.write(f"Correlation (Flood Risk vs. Opportunity): {r:.3f}\n")
        f.write(f"Statistical Significance (p-value): {p:.4f}\n")

        if p < 0.05 and r < 0:
            f.write("   -> RESULT: Statistically Significant Negative Correlation.\n")
            f.write(
                "   -> PROOF: As Flood Risk increases, Access to Services decreases.\n"
            )
            f.write(
                f"   -> MAGNITUDE: For every 10% increase in Flood Risk, Opportunity drops by {abs(slope) * 10:.1f} points.\n"
            )
        else:
            f.write(
                "   -> RESULT: No significant correlation found (or p-value > 0.05).\n"
            )
        f.write("\n")

        # --- SECTION D: WARD RANKINGS ---
        f.write("4. WARD RANKINGS\n")
        f.write("-" * 30 + "\n")

        # Top 5
        top5 = df.sort_values(by="UOI_Score", ascending=False).head(5)
        f.write("TOP 5 WARDS (Highest Opportunity):\n")
        for idx, row in top5.iterrows():
            f.write(
                f"   Ward {row['ward_id']} ({row['ward_name']}): Score {row['UOI_Score']} (Flood: {row['flood_risk_pct']}%)\n"
            )

        f.write("\nBOTTOM 5 WARDS (Lowest Opportunity):\n")
        bot5 = df.sort_values(by="UOI_Score", ascending=True).head(5)
        for idx, row in bot5.iterrows():
            f.write(
                f"   Ward {row['ward_id']} ({row['ward_name']}): Score {row['UOI_Score']} (Flood: {row['flood_risk_pct']}%)\n"
            )

        f.write("\n")
        f.write("==================================================\n")

    # 4. Save Ranking CSV
    cols_to_save = [
        "ward_id",
        "UOI_Score",
        "Score_Health",
        "Score_Edu",
        "Score_Mobility",
        "flood_risk_pct",
    ]
    # Check if cols exist before saving
    cols_present = [c for c in cols_to_save if c in df.columns]
    df[cols_present].sort_values(by="UOI_Score", ascending=False).to_csv(
        OUTPUT_CSV, index=False
    )

    print(f"✅ Thesis Results Compiled: {OUTPUT_REPORT}")
    print(f"✅ Ward Rankings Saved:     {OUTPUT_CSV}")


if __name__ == "__main__":
    compile_results()
