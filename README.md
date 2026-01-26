

# Urban Inequality in Vadodara
![midnight-blue](https://github.com/threed2y/URBAN-INEQUALITY-IN-BARODA/blob/main/data/City-bus/posters/baroda_midnight_blue_20260126_173308.png)
### A Spatial Analysis of Opportunity, Risk, and Accessibility

This project presents a **thesis-grade spatial analysis** of urban inequality in Vadodara, India.
It combines **accessibility modelling**, **flood exposure**, **public transport networks**, and **spatial statistics** to construct and analyze a **Urban Opportunity Index (UOI)** at the ward level.

The repository is designed for:

* 📊 Academic research & thesis evaluation
* 🗺️ Policy analysis & planning support
* 🌐 Public-facing interactive exploration

---

## 📌 Key Contributions

* **Urban Opportunity Index (UOI)**
  Composite index capturing access to:

  * Healthcare
  * Education
  * Road & highway connectivity
  * Public bus transit (integrated from Smart City Bus data)

* **Flood & Environmental Risk Assessment**

* **Spatial Inequality Metrics**

  * Gini coefficient
  * Lorenz curve
  * Kolm–Pollak EDE (inequality-adjusted opportunity)

* **Spatial Autocorrelation**

  * Global Moran’s I
  * LISA cluster maps

* **Interactive & Presentation-Ready Maps**

  * Satellite + physical basemaps
  * Road network overlays
  * Bus stop networks
  * Toggleable analytical layers

---

## 🗂 Repository Structure

```text
URBAN-INEQUALITY-IN-BARODA/
│
├── data/
│   ├── raw/                # Raw inputs (OSM, bus stops JSON)
│   ├── interim/            # Cleaned spatial layers
│   └── processed/          # Final analytical datasets (GPKG / CSV)
│
├── scripts/
│   └── Python/
│       ├── 03_accessibility_engine.py
│       ├── 03b_transit_accessibility.py
│       ├── 04_risk_assessment.py
│       ├── 05_calculate_uoi.py
│       ├── 06_dashboard_generator.py
│       ├── 07_*_presentation_maps.py
│       ├── 08_*_network_maps.py
│       └── 09_interactive_road_bus_network.py
│
├── results/
│   ├── thesis_figures_clean/        # Publication-ready figures
│   ├── interactive_network_maps/    # Interactive HTML maps
│   ├── interactive_physical_maps/
│   └── reports & CSV outputs
│
├── docs/
│   ├── maps/               # GitHub Pages assets
│   └── images/
│
└── README.md
```

---

## 🧠 Methodology Overview

### 1️⃣ Accessibility Modelling

* Road-network based travel times using **OSMnx**
* Separate treatment for:

  * Hospitals (drive)
  * Schools (walk)
  * Bus stops (walk)
  * Highway access (network proximity)

### 2️⃣ Transit Integration (NEW)

* Bus stop & route data from:

  * **Open Vadodara – Smart City Bus**
* Metrics derived:

  * Stop density
  * Route coverage
  * Ward-level transit accessibility

### 3️⃣ Risk & Exposure

* Flood exposure (% ward area)
* Building density (proxy for exposure intensity)

### 4️⃣ Urban Opportunity Index (UOI)

* Normalized components
* Balanced weighting
* Final scale: **0–100 (higher = better)**

### 5️⃣ Inequality & Spatial Analysis

* Gini & Lorenz
* Kolm–Pollak EDE (κ sensitivity)
* Moran’s I & LISA clustering

---

## 🗺️ Maps & Visual Outputs

### Static (Thesis / PDF)

* UOI choropleth
* Flood exposure map
* LISA cluster map
* Ward typology (Opportunity × Risk)

### Interactive (HTML)

* Satellite & physical basemaps
* Road network overlay
* Bus stops & transit layers
* Hover tooltips with **all indicators**
* Layer toggles for presentations

👉 Located in:
`results/interactive_network_maps/`

---

## 🚀 How to Run (Quick Start)

```bash
# Create environment
python -m venv venv
source venv/bin/activate

# Install core dependencies
pip install geopandas osmnx folium libpysal esda splot shapely pandas numpy matplotlib
```

Run scripts **in order**:

```bash
03_accessibility_engine.py
03b_transit_accessibility.py
04_risk_assessment.py
05_calculate_uoi.py
07_*_presentation_maps.py
09_interactive_road_bus_network.py

and others in order
```

---

## 🎓 Intended Use

* **Thesis defense & academic review**
* **Urban policy & planning insights**
* **Public visualization & storytelling**
* **Template for other Indian cities**

---

## ⚠️ Notes & Design Choices

* Wards are **synthetic analytical units**
* Transit data is **real but simplified**
* Interactive maps prioritized over heavy 3D tools for stability
* Kepler.gl intentionally excluded due to build constraints on Arch Linux

---

## 📬 Acknowledgements

* OpenStreetMap contributors
* Open Vadodara – Smart City Bus initiative
* Urban spatial analysis literature (Moran, Kolm–Pollak, etc.)

---

## ✨ Next Extensions (Optional)

* Time-of-day accessibility
* Scenario simulations (new bus routes)
* Policy-driven optimization

---

## 🔗 Related & Inspiring Repositories

The following repositories influenced tools, data handling, or visual design choices used in this work:

1. **Map Posters & Visual Design**
   🎨 [https://github.com/originalankur/maptoposter](https://github.com/originalankur/maptoposter)
   *High-quality cartographic posters and map aesthetics.*

2. **JSON Processing Utilities**
   🧩 [https://github.com/jhsu98/json-splitter](https://github.com/jhsu98/json-splitter)
   *Helpful for handling large and nested JSON datasets.*

3. **Open Vadodara Ecosystem**
   🌆 [https://github.com/open-vadodara](https://github.com/open-vadodara)
   *Community-driven open data and civic tech projects for Vadodara, including transit-related datasets.*
