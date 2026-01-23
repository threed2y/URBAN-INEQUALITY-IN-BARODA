import pandas as pd
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_FILE = os.path.join(BASE_DIR, "results", "ward_reference_table.csv")

# --------------------------------------------------
# HARD-CODED REFERENCE (NON-ANALYTICAL)
# --------------------------------------------------
# NOTE:
# These names are NOT used in computation.
# They exist only for interpretation, reporting, and discussion.
WARD_REFERENCE = {
    1: "Gotri",
    2: "Sayajigunj",
    3: "Fatehgunj",
    4: "Karelibaug",
    5: "Alkapuri",
    6: "Akota",
    7: "Atladara",
    8: "Manjalpur",
    9: "Tarsali",
    10: "Makarpura",
    11: "Waghodia Road",
    12: "Harni",
    13: "Sama",
    14: "Chhani",
    15: "Nizampura",
    16: "Ajwa Road",
    17: "Dabhoi Road",
    18: "Vasna",
    19: "Central Vadodara",
}


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def create_reference_table():
    print("--- STEP 15A: CREATING WARD REFERENCE TABLE (NON-ANALYTICAL) ---")

    df = pd.DataFrame(
        {
            "ward_id": list(WARD_REFERENCE.keys()),
            "representative_area": list(WARD_REFERENCE.values()),
        }
    )

    # --------------------------------------------------
    # TRANSPARENCY METADATA (VIVA-SAFE)
    # --------------------------------------------------
    df["basis"] = "Dominant locality overlap (manual interpretation)"
    df["analytical_status"] = "Reference only (not used in computation)"
    df["note"] = (
        "Ward boundaries are synthetic analytical units generated via spatial clustering. "
        "Names are indicative and used solely for interpretation and reporting."
    )

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"✅ Ward reference table saved to:\n   {OUTPUT_FILE}")
    print("   ✔ No analytical datasets were modified.")
    print("   ✔ Safe for citation, appendix use, and interpretation tables.")


if __name__ == "__main__":
    create_reference_table()
