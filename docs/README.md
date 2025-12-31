
```markdown
# 🏙️ Modeling Urban Inequality in Vadodara  
### *A Geospatial & Network-Based Analysis*

<p align="center">
  <img src="https://img.shields.io/badge/Status-Phase%201%20Complete-success" />
  <img src="https://img.shields.io/badge/Languages-Python%20%7C%20R-blue" />
  <img src="https://img.shields.io/badge/Tools-QGIS%20%7C%20OSMnx%20%7C%20sf-orange" />
</p>

---

## 📌 Project Overview
🎓 **Master’s Thesis** **Department of Statistics, The Maharaja Sayajirao University of Baroda**

This research models **urban inequality as a spatial and network phenomenon**. By constructing a **Digital Twin of Vadodara City (19 administrative wards)**, the study measures *realistic* access to essential services—**hospitals, schools, and public transport**—using **actual road networks** rather than straight-line distances.

The results are integrated into a composite **Urban Opportunity Index (UOI)** using **Principal Component Analysis (PCA)** and validated through **spatial statistical inference**.

---

## 🧠 Core Research Questions
- ❓ *Is access to public services spatially equitable across the city?*
- ❓ *Do areas of deprivation form persistent spatial clusters?*
- ❓ *Can network-based accessibility reveal inequalities hidden by city-wide averages?*

---

## 🚀 Key Features & Contributions

✨ **Primary Spatial Data Creation** - Digitized and georeferenced the **current 19-ward administrative boundary** of Vadodara.
- Addresses the critical **post-2011 Census spatial data gap**.

🛣️ **Network-Based Accessibility Modeling** - Road network sourced from **OpenStreetMap**.
- Graph scale: **50,000+ nodes**, **120,000+ edges**.
- Travel time computed using **graph theory (shortest path algorithms)**.

📊 **Urban Opportunity Index (UOI)** - Constructed via **PCA** for objective, variance-driven weighting.
- Moves beyond arbitrary index construction methods.

📍 **Spatial Statistical Validation** - **Global Moran’s I** for city-wide spatial dependence.
- **LISA (Local Moran’s I)** to identify:
  - 🔥 Hotspots of privilege
  - ❄️ Coldspots of deprivation
- Provides empirical evidence of **Spatial Traps**.

---

## 🗂️ Project Structure

```text
URBAN-INEQUALITY-IN-BARODA/
├── data/
│   ├── raw/                 # Digitized Ward Boundaries (GeoJSON)
│   ├── interim/             # Spatial Database (GeoPackage)
│   └── processed/           # Final CSVs & Index Scores
│
├── scripts/
│   ├── python/              # Data Engineering & Network Analysis
│   └── R/                   # Statistical Modeling & Inference
│
├── output/
│   └── maps/                # Final Maps & Figures
│
├── docs/                    # Methodology & Academic Justifications
├── requirements.txt
├── install_packages.R
└── README.md

```

---

## 🖼️ Visual Outputs & Figures

### 🗺️ Figure 1: Urban Opportunity Index (UOI)

*Spatial distribution of opportunity across Vadodara wards.*

### 🔥 Figure 2: LISA Cluster Map (Hotspots & Coldspots)

*Local clusters of statistically significant high and low opportunity.*

### 📈 Figure 3: Moran’s I Scatter Plot

*Global spatial autocorrelation diagnostic.*

---

## 📊 Key Findings — Phase 1

| 📌 Metric | 📈 Result | 🧠 Interpretation |
| --- | --- | --- |
| 🏆 **Most Privileged Ward** | **Ward 12** (UOI = 100.0) | Excellent hospital access, dense road connectivity. |
| ⚠️ **Most Deprived Ward** | **Ward 14** (UOI = 0.0) | Identified as a structural *Service Desert*. |
| 🌍 **Global Moran’s I** | `0.056` (p > 0.05) | Inequality is **not random**; it follows specific patterns. |
| 🧩 **LISA Analysis** | Significant Clusters | West: *Privilege Corridor* · Center: *Poverty Trap*. |

---

## 🏛️ Policy Implications

This research demonstrates that **urban inequality is spatially entrenched**, not evenly distributed.

**1️⃣ Targeted Infrastructure Investment**
Low-Low (LL) clusters represent **persistent deprivation zones**. Blanket city-wide policies miss these areas; **ward-specific service upgrades** are required.

**2️⃣ Rethinking “Average City” Metrics**
City-wide means obscure **localized service deserts**. Spatial diagnostics must complement traditional indicators.

**3️⃣ Transport as an Equalizer**
Poor accessibility often stems from **network disconnectivity**, not just distance. Improving road and transit connectivity can yield **high equity returns**.

**4️⃣ Evidence-Based Urban Planning**
UOI + LISA maps act as **decision-support tools** for facility placement, transport routing, and resource prioritization.

---

## 🔮 Phase 2 — Model Validation (Ongoing)

To ground-truth results, a **Stratified Random Household Survey** is being conducted.

* **Stratification:** High / Medium / Low UOI wards.
* **Sample Size:** ~200 households (via Cochran’s Formula).
* **Objective:** Correlate *modeled accessibility* with *citizen-perceived accessibility* to validate spatial inequality from lived experience.

---

## ✍️ Author

**Ethan Hunt** 

🎓 Master’s Student — Statistics

🏫 The Maharaja Sayajirao University of Baroda

📧 [ethanonarch025@proton.me](mailto:ethanonarch025@proton.me)

---

## 📜 Disclaimer

This project is developed **strictly for academic and research purposes**. All spatial outputs are **analytical abstractions** and should not be interpreted as official planning documents.

---

*“Cities are not just built — they are experienced. This work attempts to measure that experience, spatially.”*

```

```