import pandas as pd
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REFERENCE_TABLE = os.path.join(BASE_DIR, "results", "ward_reference_table.csv")

EXPECTED_WARDS = set(range(1, 20))  # 19 synthetic wards (fixed by design)


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def validate_reference():
    print("--- STEP 16: VALIDATING WARD REFERENCE TABLE (NON-ANALYTICAL) ---")

    # --------------------------------------------------
    # 1. FILE EXISTENCE
    # --------------------------------------------------
    if not os.path.exists(REFERENCE_TABLE):
        raise FileNotFoundError(
            "❌ Ward reference table not found.\n"
            "👉 Run STEP 15A to create ward_reference_table.csv"
        )

    df = pd.read_csv(REFERENCE_TABLE)

    # --------------------------------------------------
    # 2. STRUCTURAL CHECKS
    # --------------------------------------------------
    required_cols = {"ward_id", "representative_area"}
    missing_cols = required_cols - set(df.columns)

    if missing_cols:
        raise ValueError(f"❌ Missing required columns: {missing_cols}")

    # --------------------------------------------------
    # 3. ID CONSISTENCY CHECK
    # --------------------------------------------------
    found = set(df["ward_id"])
    missing_ids = EXPECTED_WARDS - found
    extra_ids = found - EXPECTED_WARDS

    if missing_ids:
        raise ValueError(
            f"❌ Missing ward IDs in reference table: {sorted(missing_ids)}"
        )
    if extra_ids:
        raise ValueError(
            f"❌ Unexpected ward IDs in reference table: {sorted(extra_ids)}"
        )

    # --------------------------------------------------
    # 4. DUPLICATE CHECK
    # --------------------------------------------------
    if df["ward_id"].duplicated().any():
        dupes = df[df["ward_id"].duplicated()]["ward_id"].tolist()
        raise ValueError(f"❌ Duplicate ward IDs found: {dupes}")

    # --------------------------------------------------
    # 5. FINAL CONFIRMATION
    # --------------------------------------------------
    print("✅ Ward reference table is complete, unique, and consistent.")
    print("   ✔ All 19 synthetic wards accounted for")
    print("   ✔ No unexpected or duplicate IDs")
    print("   ✔ No analytical datasets were modified")
    print("   ✔ Names remain external interpretive metadata only")


if __name__ == "__main__":
    validate_reference()
