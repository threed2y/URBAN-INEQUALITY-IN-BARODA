import os
import shutil
import datetime

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "thesis_figures_clean")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

MAPS_DIR = os.path.join(DOCS_DIR, "maps")
IMAGES_DIR = os.path.join(DOCS_DIR, "images")

os.makedirs(MAPS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# --------------------------------------------------
# SINGLE SOURCE OF TRUTH (UPDATED FIGURES)
# --------------------------------------------------
FIGURES = {
    "vulnerability": "Figure_14_Flood_vs_UOI.png",
    "distribution": "Figure_15_UOI_Distribution.png",
    "lorenz": "Figure_16_Lorenz_Curve.png",
    "lisa": "Figure_18_LISA_Clusters.png",
}

INTERACTIVE_MAPS = [
    "map_01_opportunity_index.html",
    "map_02_flood_vulnerability.html",
]


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def update_site():
    print("--- STEP 11 (FINAL): UPDATING GITHUB PAGES ---")

    build_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # --------------------------------------------------
    # 1. SYNC INTERACTIVE MAPS
    # --------------------------------------------------
    print("-> Syncing interactive maps...")
    for m in INTERACTIVE_MAPS:
        src = os.path.join(RESULTS_DIR, m)
        dst = os.path.join(MAPS_DIR, m)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"   ✓ {m}")
        else:
            print(f"   ⚠️ Missing map: {m}")

    # --------------------------------------------------
    # 2. SYNC STATISTICAL FIGURES
    # --------------------------------------------------
    print("-> Syncing statistical figures...")
    missing = []

    for key, fname in FIGURES.items():
        src = os.path.join(FIGURES_DIR, fname)
        dst = os.path.join(IMAGES_DIR, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"   ✓ {fname}")
        else:
            missing.append(fname)

    if missing:
        print("⚠️ Missing expected figures:")
        for f in missing:
            print(f"   - {f}")

    # --------------------------------------------------
    # 3. GENERATE ANALYSIS REPORT (MARKDOWN)
    # --------------------------------------------------
    report_path = os.path.join(DOCS_DIR, "analysis_report.md")
    print(f"-> Generating analysis report: {report_path}")

    with open(report_path, "w") as f:
        f.write("---\n")
        f.write("layout: default\n")
        f.write("title: Spatial Analysis Results\n")
        f.write("---\n\n")

        f.write("# Spatial Analysis of Urban Opportunity in Vadodara\n\n")
        f.write(f"*Build timestamp: {build_time}*\n\n")
        f.write(
            "*All results are based on the balanced Urban Opportunity Index (UOI).*\n\n"
        )

        # --------------------------------------------------
        # MAPS
        # --------------------------------------------------
        f.write("## 1. Interactive Spatial Maps\n\n")
        f.write("| Opportunity Index | Flood Vulnerability |\n")
        f.write("| :---: | :---: |\n")
        f.write(
            "| [Launch Map](maps/map_01_opportunity_index.html) | "
            "[Launch Map](maps/map_02_flood_vulnerability.html) |\n\n"
        )

        # --------------------------------------------------
        # STATISTICAL EVIDENCE
        # --------------------------------------------------
        f.write("## 2. Statistical Evidence\n\n")

        f.write("### 2.1 Flood Risk and Opportunity\n\n")
        f.write(
            "This figure evaluates the relationship between flood exposure and "
            "urban opportunity across analytical wards.\n\n"
        )
        f.write(f"![Flood vs Opportunity](images/{FIGURES['vulnerability']})\n\n")

        f.write("### 2.2 Distribution of Urban Opportunity\n\n")
        f.write(
            "The distribution illustrates variation in opportunity levels, "
            "indicating unequal access within the city.\n\n"
        )
        f.write(f"![Distribution](images/{FIGURES['distribution']})\n\n")

        f.write("### 2.3 Inequality in Opportunity (Lorenz Curve)\n\n")
        f.write(
            "Deviation from the line of perfect equality reflects the degree of "
            "inequality in opportunity distribution.\n\n"
        )
        f.write(f"![Lorenz Curve](images/{FIGURES['lorenz']})\n\n")

        f.write("### 2.4 Spatial Clustering of Opportunity\n\n")
        f.write(
            "Local Indicators of Spatial Association (LISA) reveal statistically "
            "significant clusters of high and low opportunity.\n\n"
        )
        f.write(f"![LISA](images/{FIGURES['lisa']})\n")

    print("\n✅ GitHub Pages site successfully updated.")
    print("👉 Review: docs/analysis_report.md")


if __name__ == "__main__":
    update_site()
