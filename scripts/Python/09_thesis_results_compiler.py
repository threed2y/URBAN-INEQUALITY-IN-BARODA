import geopandas as gpd
import pandas as pd
import numpy as np
import os
from scipy.stats import pearsonr, linregress

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)
OUTPUT_REPORT = os.path.join(BASE_DIR, "results", "FINAL_THESIS_RESULTS.txt")
OUTPUT_CSV = os.path.join(BASE_DIR, "results", "ward_rankings.csv")


# --------------------------------------------------
# GINI COEFFICIENT
# --------------------------------------------------
def gini(array):
    array = np.array(array, dtype=float).flatten()
    if np.any(array < 0):
        array -= np.min(array)
    array = np.sort(array)
    n = len(array)
    index = np.arange(1, n + 1)
    return np.sum((2 * index - n - 1) * array) / (n * np.sum(array))


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def compile_results():
    print("--- STEP 9 (FINAL): THESIS RESULTS COMPILATION ---")

    if not os.path.exists(INPUT_GPKG):
        raise FileNotFoundError("Balanced UOI file not found.")

    # --------------------------------------------------
    # LOAD & CLEAN DATA
    # --------------------------------------------------
    gdf = gpd.read_file(INPUT_GPKG)
    df = pd.DataFrame(gdf.drop(columns="geometry"))

    # Critical safety step
    df = df.dropna(subset=["UOI_Score"]).reset_index(drop=True)
    n = len(df)

    print(f"-> Wards included in analysis: {n}")

    # --------------------------------------------------
    # WRITE RESULTS REPORT
    # --------------------------------------------------
    with open(OUTPUT_REPORT, "w") as f:
        f.write("=" * 50 + "\n")
        f.write(" URBAN OPPORTUNITY & INEQUALITY IN VADODARA\n")
        f.write("=" * 50 + "\n\n")

        # --------------------------------------------------
        # 1. CITY OVERVIEW
        # --------------------------------------------------
        f.write("1. CITY-WIDE OVERVIEW\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total Wards Analysed: {n}\n")
        f.write(f"Mean Urban Opportunity Index (UOI): {df['UOI_Score'].mean():.2f}\n")
        f.write(f"Mean Flood Risk: {df['flood_exposure_pct'].mean():.2f}%\n")
        f.write(
            f"Mean Hospital Access Time: {df['hospitals_min'].mean():.1f} minutes\n"
        )
        f.write(
            f"Mean School Access Time:   {df['schools_min'].mean():.1f} minutes\n\n"
        )

        # --------------------------------------------------
        # 2. INEQUALITY METRICS
        # --------------------------------------------------
        f.write("2. INEQUALITY METRICS\n")
        f.write("-" * 30 + "\n")

        gini_score = gini(df["UOI_Score"])
        f.write(f"Gini Coefficient (Opportunity): {gini_score:.3f}\n")

        if gini_score > 0.4:
            f.write("Interpretation: High inequality (severe structural gaps).\n")
        elif gini_score > 0.3:
            f.write("Interpretation: Moderate inequality.\n")
        else:
            f.write("Interpretation: Relatively low inequality.\n")

        top_10 = df["UOI_Score"].quantile(0.90)
        bot_10 = df["UOI_Score"].quantile(0.10)
        gap_ratio = top_10 / bot_10 if bot_10 > 0 else np.nan

        f.write(f"Privilege Gap (Top 10% / Bottom 10%): {gap_ratio:.1f}×\n\n")

        # --------------------------------------------------
        # 3. VULNERABILITY TRAP
        # --------------------------------------------------
        f.write("3. FLOOD RISK AND OPPORTUNITY RELATIONSHIP\n")
        f.write("-" * 30 + "\n")

        r, p = pearsonr(df["flood_exposure_pct"], df["UOI_Score"])
        slope, _, _, _, _ = linregress(df["flood_exposure_pct"], df["UOI_Score"])

        f.write(f"Pearson Correlation (r): {r:.3f}\n")
        f.write(f"P-value: {p:.4f}\n")

        if p < 0.05:
            f.write(
                "Result: Statistically significant negative association.\n"
                f"Interpretation: A 10% increase in flood risk is associated with "
                f"a {abs(slope) * 10:.1f}-point reduction in UOI.\n\n"
            )
        else:
            f.write("Result: No statistically significant relationship detected.\n\n")

        # --------------------------------------------------
        # 4. WARD RANKINGS (IDENTIFIER ONLY)
        # --------------------------------------------------
        f.write("4. WARD RANKINGS (BY UOI SCORE)\n")
        f.write("-" * 30 + "\n")

        top5 = df.sort_values("UOI_Score", ascending=False).head(5)
        bot5 = df.sort_values("UOI_Score", ascending=True).head(5)

        f.write("Top 5 Wards:\n")
        for _, r_ in top5.iterrows():
            f.write(
                f"  Ward {int(r_['ward_id'])}: "
                f"UOI = {r_['UOI_Score']:.2f}, Flood Risk = {r_['flood_exposure_pct']:.1f}%\n"
            )

        f.write("\nBottom 5 Wards:\n")
        for _, r_ in bot5.iterrows():
            f.write(
                f"  Ward {int(r_['ward_id'])}: "
                f"UOI = {r_['UOI_Score']:.2f}, Flood Risk = {r_['flood_exposure_pct']:.1f}%\n"
            )

        f.write("\n" + "=" * 50 + "\n")

    # --------------------------------------------------
    # SAVE RANKINGS CSV
    # --------------------------------------------------
    df[
        [
            "ward_id",
            "UOI_Score",
            "Score_Health",
            "Score_Edu",
            "Score_Mobility",
            "flood_exposure_pct",
        ]
    ].sort_values("UOI_Score", ascending=False).to_csv(OUTPUT_CSV, index=False)

    print(f"✅ Final results report saved: {OUTPUT_REPORT}")
    print(f"✅ Ward rankings CSV saved:  {OUTPUT_CSV}")


if __name__ == "__main__":
    compile_results()
