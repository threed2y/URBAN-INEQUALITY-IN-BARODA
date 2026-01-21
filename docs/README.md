# Modeling Urban Inequality in Vadodara: A Spatial Data Science Approach

### *The "Vulnerability Trap" — Where Flood Risk Meets Deprivation*

**Master’s Thesis Project** **Department of Statistics** **The Maharaja Sayajirao University of Baroda**

![Thesis Dashboard](output/maps/thesis_dashboard_v2.png)
*(Above: The Urban Opportunity Index Map, visualizing the divide between the privileged core and the vulnerable periphery.)*

---

## 🎯 Motivation: The "Double Burden" of Place
Urban inequality is rarely random. It is structurally shaped by **where people live**, **how they move**, and **how infrastructure is distributed**.

In rapidly growing cities like Vadodara, "city-wide averages" conceal a harsh reality:
* **The Access Divide:** While the historic core enjoys rapid access to hospitals and schools, the developing periphery faces "Service Deserts."
* **The Risk Nexus:** The poorest access often overlaps with the highest environmental risks (Flooding), creating a **"Vulnerability Trap"** that is impossible to escape without structural intervention.

Traditional economic metrics miss this. **Spatial Data Science reveals it.**

---

## 🚀 Core Contribution
This project moves beyond simple density mapping to model the city as a complex, interactive system.

1.  **Network-Based Accessibility:**
    * We do not use straight lines. We model the city as a **Graph ($G=\{N,E\}$)** to measure the *true cost* of travel (in minutes) through traffic, winding roads, and barriers.
2.  **The Urban Opportunity Index (UOI):**
    * A composite metric that integrates **Health**, **Education**, **Mobility**, and **Flood Risk** into a single "Spatial Justice Score" for every ward.
3.  **Statistical Proof of Segregation:**
    * Using **Moran’s I** and **LISA Clustering**, we mathematically prove that inequality in Vadodara is not random—it is structurally segregated.

---

## 🗺️ Explore the Findings

### [**🌍 Launch Interactive Maps**](maps/map_01_opportunity_index.html)
Explore the high-resolution, interactive visualizations of the city.
* **Opportunity Map:** See which wards are "Privileged" vs. "Deprived."
* **Vulnerability Map:** See the "Blue Corridor" of flood risk along the Vishwamitri.

### [**📊 See the Evidence**](analysis_report.md)
View the statistical proofs behind the thesis.
* **The Vulnerability Trap:** Scatter plots proving the link between Flood Risk and Poverty.
* **The Privilege Gap:** The Lorenz Curve of Vadodara.

---

## 📂 Project Structure

This repository is organized to ensure **Reproducibility** and **Transparency**:

* **`/data`**: The raw geospatial inputs (Shapefiles, OSM Graphs, Census Data).
* **`/scripts`**: The Python ETL pipeline (Extraction, Transformation, Analysis).
    * `01-04`: Data Engineering & Network Analysis.
    * `05-06`: Index Calculation & Map Generation.
    * `07-10`: Statistical Validation (Regression, Gini, Moran's I).
* **`/results`**: The final output—High-res Maps, Tables, and Statistical Plots.
* **`/docs`**: The source code for this documentation website.

---

*This project was developed using **Python**, **OSMnx**, **GeoPandas**, and **PySAL**.*
