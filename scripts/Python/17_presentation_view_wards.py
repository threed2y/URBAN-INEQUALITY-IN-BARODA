import pandas as pd
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RANKINGS = os.path.join(BASE_DIR, "results", "ward_rankings.csv")
REFERENCE = os.path.join(BASE_DIR, "results", "ward_reference_table.csv")
OUTPUT = os.path.join(BASE_DIR, "results", "ward_rankings_display.csv")

EXPECTED_WARDS = set(range(1, 20))  # 19 synthetic wards


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def generate_display_table():
    print("--- STEP 17A: GENERATING DISPLAY-ONLY RANKING TABLE ---")

    # --------------------------------------------------
    # 1. FILE CHECKS
    # --------------------------------------------------
    if not os.path.exists(RANKINGS):
        raise FileNotFoundError("❌ ward_rankings.csv not found. Run STEP 9 first.")

    if not os.path.exists(REFERENCE):
        raise FileNotFoundError(
            "❌ ward_reference_table.csv not found. Run STEP 15A first."
        )

    # --------------------------------------------------
    # 2. LOAD DATA
    # --------------------------------------------------
    df_rank = pd.read_csv(RANKINGS)
    df_ref = pd.read_csv(REFERENCE)[["ward_id", "representative_area"]]

    # --------------------------------------------------
    # 3. VALIDATION (NON-ANALYTICAL)
    # --------------------------------------------------
    missing_ids = EXPECTED_WARDS - set(df_rank["ward_id"])
    if missing_ids:
        raise ValueError(f"❌ Rankings missing ward IDs: {sorted(missing_ids)}")

    # --------------------------------------------------
    # 4. MERGE (LEFT JOIN — PRESERVES ANALYTICAL ORDER)
    # --------------------------------------------------
    df_disp = df_rank.merge(df_ref, on="ward_id", how="left")

    # --------------------------------------------------
    # 5. COLUMN ORDER (HUMAN-READABLE)
    # --------------------------------------------------
    cols = ["ward_id", "representative_area"] + [
        c for c in df_disp.columns if c not in ["ward_id", "representative_area"]
    ]
    df_disp = df_disp[cols]

    # --------------------------------------------------
    # 6. EXPLICIT DISCLAIMER
    # --------------------------------------------------
    df_disp["note"] = (
        "Representative area names are indicative only. "
        "Rankings are computed exclusively using synthetic ward IDs."
    )

    # --------------------------------------------------
    # 7. SAVE
    # --------------------------------------------------
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    df_disp.to_csv(OUTPUT, index=False)

    print(f"✅ Display-only ranking table created:\n   {OUTPUT}")
    print("   ✔ No analytical datasets were modified")
    print("   ✔ Names are external interpretive metadata only")


if __name__ == "__main__":
    generate_display_table()
