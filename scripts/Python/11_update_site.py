import os
import shutil
import datetime

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
PROOFS_DIR = os.path.join(RESULTS_DIR, "thesis_proofs")
DOCS_DIR = os.path.join(BASE_DIR, "docs")


def update_site():
    print("--- STEP 11: UPDATING GITHUB PAGES ---")

    # 1. Ensure Directories Exist
    maps_dir = os.path.join(DOCS_DIR, "maps")
    img_dir = os.path.join(DOCS_DIR, "images")
    os.makedirs(maps_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)

    # 2. Sync Interactive Maps
    print("-> Syncing Maps...")
    # We specifically look for the professional maps we made in Step 6
    target_maps = ["map_01_opportunity_index.html", "map_02_flood_vulnerability.html"]

    for map_name in target_maps:
        src = os.path.join(RESULTS_DIR, map_name)
        if os.path.exists(src):
            dst = os.path.join(maps_dir, map_name)
            shutil.copy2(src, dst)
            print(f"   + Updated: docs/maps/{map_name}")
        else:
            print(f"   ⚠️ Warning: Could not find {map_name}. Run Step 6.")

    # 3. Sync Statistical Proofs
    print("-> Syncing Graphs...")
    if os.path.exists(PROOFS_DIR):
        for f in os.listdir(PROOFS_DIR):
            if f.endswith(".png"):
                src = os.path.join(PROOFS_DIR, f)
                dst = os.path.join(img_dir, f)
                shutil.copy2(src, dst)
                print(f"   + Updated: docs/images/{f}")
    else:
        print("   ⚠️ Warning: No proofs folder found. Run Step 10.")

    # 4. Generate 'Analysis Report' Page
    # We create a specific Markdown file for these results so we don't overwrite your main index.
    report_path = os.path.join(DOCS_DIR, "analysis_report.md")
    print(f"-> Generating Report Page: {report_path}")

    with open(report_path, "w") as f:
        f.write("---\nlayout: default\ntitle: Spatial Analysis Results\n---\n\n")
        f.write("# 🏙️ Spatial Analysis Findings\n")
        f.write(f"*Last Updated: {datetime.date.today()}*\n\n")

        f.write("## 1. Interactive Maps\n")
        f.write(
            "Explore the spatial distribution of opportunity and risk in Vadodara.\n\n"
        )
        f.write("| **Opportunity Map** | **Vulnerability Map** |\n")
        f.write("| :---: | :---: |\n")
        f.write(
            "| [**Launch Map**](maps/map_01_opportunity_index.html) | [**Launch Map**](maps/map_02_flood_vulnerability.html) |\n"
        )
        f.write("| *Shows Access to Health/Edu* | *Shows Flood Risk Zones* |\n\n")

        f.write("## 2. Statistical Evidence\n")
        f.write("### The 'Vulnerability Trap'\n")
        f.write(
            "There is a statistically significant negative correlation between Flood Risk and Urban Opportunity. "
            "As flood risk increases, access to critical services decreases.\n\n"
        )
        f.write("![Vulnerability Trap](images/Figure_01_Vulnerability_Trap.png)\n\n")

        f.write("### Structural Inequality (Lorenz Curve)\n")
        f.write(
            "The gap between the red curve (Vadodara) and the black line (Perfect Equality) represents the 'Privilege Gap'.\n\n"
        )
        f.write("![Lorenz Curve](images/Figure_03_Lorenz_Curve.png)\n\n")

        f.write("### Spatial Segregation\n")
        f.write(
            "Inequality is not random. The LISA Cluster map identifies 'Deprivation Pockets' (Blue) that are structurally separated from 'Elite Enclaves' (Red).\n\n"
        )
        f.write("![Segregation Map](images/Figure_05_Segregation_Map.png)\n")

    print("\n✅ Site Updated!")
    print("   👉 Check 'docs/analysis_report.md' to see your generated page.")


if __name__ == "__main__":
    update_site()
