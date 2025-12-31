

```markdown
# Modeling Urban Inequality in Vadodara: A Geospatial & Network Analysis

![Status](https://img.shields.io/badge/Status-Phase%201%20Complete-success)
![Language](https://img.shields.io/badge/Languages-Python%20%7C%20R-blue)
![Tools](https://img.shields.io/badge/Tools-QGIS%20%7C%20OSMnx%20%7C%20sf-orange)

## 📌 Project Overview
**Master's Thesis | Department of Statistics, The Maharaja Sayajirao University of Baroda**

This project constructs a **"Digital Twin"** of Vadodara City (19 Administrative Wards) to quantify urban inequality. Unlike traditional studies that use straight-line distances, this research utilizes **Graph Theory** on the actual road network to measure the realistic time-cost of accessing critical public services (Hospitals, Schools, Transport).

The findings are synthesized into a composite **Urban Opportunity Index (UOI)** using Principal Component Analysis (PCA) to identify statistically significant clusters of privilege and deprivation.

---

## 🚀 Key Features
* **Primary Data Creation:** Manually digitized and georeferenced the current 19-Ward administrative map of Vadodara (filling the data gap from the 2011 Census).
* **Network Analysis:** Calculated travel time matrices using the OpenStreetMap (OSM) driving/walking graph (Nodes: 50k+, Edges: 120k+).
* **Multidimensional Indexing:** Constructed the UOI using PCA to weight services based on variance rather than arbitrary selection.
* **Spatial Statistics:** Applied Global Moran’s I and LISA (Local Indicators of Spatial Association) to prove the existence of "Spatial Traps" (clustered inequality).

---

## 📂 Project Structure
```text
URBAN-INEQUALITY-IN-BARODA/
├── data/
│   ├── raw/                 # Digitized GeoJSONs (Wards)
│   ├── interim/             # Spatial Database (GPKG)
│   └── processed/           # Final CSVs and Index Scores
├── docs/                    # Methodology Logs & Academic Justifications
├── output/
│   └── maps/                # Final Choropleth & Cluster Maps (PNG)
├── scripts/
│   ├── python/              # Data Engineering & Network Analysis
│   │   ├── 01_build_database.py
│   │   └── 02_network_analysis.py
│   └── R/                   # Statistical Modeling & Inference
│       ├── 03_construct_index.R
│       ├── 04_spatial_statistics.R
│       └── 05_sample_size.R
├── requirements.txt         # Python Dependencies
├── install_packages.R       # R Dependencies
└── README.md                # Project Documentation

```

---

## 📊 Key Findings (Phase 1)

| Metric | Result | Interpretation |
| --- | --- | --- |
| **Most Privileged** | **Ward 12** (Score: 100.0) | < 5 min drive to hospital, high walkability. |
| **Most Deprived** | **Ward 14** (Score: 0.0) | A structural "Service Desert" with poor connectivity. |
| **Global Moran's I** | `0.056` (p > 0.05) | Inequality is **not** defined by a simple North-South divide. |
| **LISA Analysis** | **Significant Clusters** | A distinct "Corridor of Privilege" (West) and "Poverty Trap" (Center) exist. |

---

## 🛠️ Installation & Usage

### 1. Prerequisites

* **System:** Linux (Arch/Ubuntu) recommended for geospatial libraries.
* **Tools:** Python 3.9+, R 4.0+, GDAL/GEOS system libraries.

### 2. Setup Environment

```bash
# Clone the repository
git clone [https://github.com/yourusername/urban-inequality-vadodara.git](https://github.com/yourusername/urban-inequality-vadodara.git)
cd URBAN-INEQUALITY-IN-BARODA

# Install Python Dependencies
pip install -r requirements.txt

# Install R Dependencies
Rscript install_packages.R

```

### 3. Running the Pipeline

The project is designed to run sequentially:

**Step 1: Build the Spatial Database** (Merges raw GeoJSONs)

```bash
python3 scripts/python/01_build_database.py

```

**Step 2: Run Network Analysis** (Downloads OSM graph & calculates travel times)

```bash
python3 scripts/python/02_network_analysis.py

```

**Step 3: Construct the Index** (Runs PCA in R)

```bash
Rscript scripts/R/03_construct_index.R

```

**Step 4: Spatial Statistics** (Generates Cluster Maps)

```bash
Rscript scripts/R/04_spatial_statistics.R

```

---

## 🔮 Phase 2: Validation (Current Work)

We are currently conducting a **Stratified Random Survey** to ground-truth the model.

* **Sampling Strategy:** Stratified by UOI Score (High/Medium/Low Wards).
* **Sample Size:** ~200 Households (calculated via Cochran’s Formula).
* **Objective:** To correlate *calculated* accessibility (Model) with *perceived* accessibility (Citizens).

---

## ✍️ Author

**[Your Name]**

* Master's Student, Statistics
* The Maharaja Sayajirao University of Baroda
* *Contact: [ethanonarch025@proton.me]*

```

```