import pandas as pd
import os

OUTPUT_FILE = "results/ward_identities.csv"


def force_names():
    print("--- FINALIZING WARD NAMES FOR THESIS ---")

    # Matches the table above
    data = [
        {"Ward_ID": 1, "Identified_Area": "Chhani"},
        {"Ward_ID": 2, "Identified_Area": "Sama-Savli"},
        {"Ward_ID": 3, "Identified_Area": "Fatehgunj"},
        {"Ward_ID": 4, "Identified_Area": "Nizampura"},
        {"Ward_ID": 5, "Identified_Area": "Karelibaug"},
        {"Ward_ID": 6, "Identified_Area": "Sayajigunj"},
        {"Ward_ID": 7, "Identified_Area": "Raopura"},
        {"Ward_ID": 8, "Identified_Area": "Gorwa"},
        {"Ward_ID": 9, "Identified_Area": "Gotri"},
        {"Ward_ID": 10, "Identified_Area": "Bhayli"},
        {"Ward_ID": 11, "Identified_Area": "Vasna-Bhayli"},
        {"Ward_ID": 12, "Identified_Area": "Waghodia Road"},
        {"Ward_ID": 13, "Identified_Area": "Mandvi / Panigate"},
        {"Ward_ID": 14, "Identified_Area": "Nava Bazaar"},
        {"Ward_ID": 15, "Identified_Area": "Ajwa Road"},
        {"Ward_ID": 16, "Identified_Area": "Makarpura (GIDC)"},
        {"Ward_ID": 17, "Identified_Area": "Maneja"},
        {"Ward_ID": 18, "Identified_Area": "Tarsali"},
        {"Ward_ID": 19, "Identified_Area": "Atladara"},
    ]

    df = pd.DataFrame(data)
    os.makedirs("results", exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Ward Reference Table saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    force_names()
