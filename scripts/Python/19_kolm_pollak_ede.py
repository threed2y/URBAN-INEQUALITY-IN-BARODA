import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)
OUTPUT_TABLE = os.path.join(BASE_DIR, "results", "EDE_Opportunity_Table.csv")
OUTPUT_FIG = os.path.join(
    BASE_DIR, "results", "thesis_figures_clean", "Figure_17_EDE_Sensitivity.png"
)

os.makedirs(os.path.dirname(OUTPUT_FIG), exist_ok=True)


# --------------------------------------------------
# KOLM–POLLACK EDE FUNCTION
# --------------------------------------------------
def kolm_pollak_ede(values, kappa):
    """
    Kolm–Pollak Equally Distributed Equivalent (EDE)
    values : normalized opportunity scores (0–1, higher = better)
    kappa  : inequality aversion parameter (>0)
    """
    values = np.asarray(values)
    return -(1 / kappa) * np.log(np.mean(np.exp(-kappa * values)))


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def compute_ede():
    print("--- STEP 21: KOLM–POLLACK EDE (INEQUALITY-ADJUSTED OPPORTUNITY) ---")

    gdf = gpd.read_file(INPUT_GPKG)

    # --------------------------------------------------
    # CLEAN & NORMALIZE (CRITICAL)
    # --------------------------------------------------
    uoi = gdf["UOI_Score"].dropna().values

    # Normalize to [0,1] for welfare interpretation
    uoi_norm = (uoi - uoi.min()) / (uoi.max() - uoi.min())

    # FIX I-12: epsilon must NOT be added before normalisation — it shifts
    # the welfare floor and understates the inequality penalty.
    # Add only if a ward genuinely has UOI = 0 (floor case).
    if (uoi_norm == 0).any():
        uoi_norm = uoi_norm + 1e-9   # minimal correction only when strictly needed

    mean_uoi = uoi_norm.mean()

    # --------------------------------------------------
    # INEQUALITY AVERSION PARAMETERS
    # Updated to welfare-standard range per IMF / World Bank literature:
    #   kappa = 0.5  — mild aversion (IMF baseline)
    #   kappa = 1.0  — moderate aversion (World Bank standard)
    #   kappa = 2.0  — strong aversion (Atkinson-equivalent)
    # Previous values [0.1, 0.25, 0.5] were too low for urban inequality work.
    # --------------------------------------------------
    kappas = [0.5, 1.0, 2.0]

    records = []

    for k in kappas:
        ede     = kolm_pollak_ede(uoi_norm, k)
        penalty = mean_uoi - ede

        records.append(
            {
                "kappa": k,
                "Mean_UOI_(0-1)": round(mean_uoi, 3),
                "EDE_UOI_(0-1)": round(ede, 3),
                "Inequality_Penalty": round(penalty, 3),
            }
        )

        print(f"k={k}: Mean={mean_uoi:.3f}, EDE={ede:.3f}, Penalty={penalty:.3f}")
    df_out.to_csv(OUTPUT_TABLE, index=False)

    print(f"✅ EDE results saved to: {OUTPUT_TABLE}")

    # --------------------------------------------------
    # FORMAL SENSITIVITY PLOT
    # --------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))

    ax.plot(
        df_out["kappa"],
        df_out["EDE_UOI_(0-1)"],
        marker="o",
        linewidth=2,
        color="#b2182b",
        label="Inequality-adjusted Opportunity (EDE)",
    )

    ax.axhline(
        mean_uoi,
        linestyle="--",
        color="black",
        linewidth=1,
        label="Mean Opportunity",
    )

    ax.set_title("Sensitivity of Opportunity to Inequality Aversion")
    ax.set_xlabel("Inequality Aversion Parameter (κ)")
    ax.set_ylabel("Opportunity (Normalized 0–1)")

    ax.legend(frameon=False)
    ax.grid(False)

    plt.tight_layout()
    plt.savefig(OUTPUT_FIG, dpi=300)
    plt.close()

    print(f"✅ EDE sensitivity figure saved to: {OUTPUT_FIG}")


if __name__ == "__main__":
    compute_ede()
