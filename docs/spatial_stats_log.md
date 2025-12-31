# Step 4: Spatial Autocorrelation Analysis (Moran's I)

**Date:** December 31, 2025
**Objective:** To determine if the spatial distribution of the Urban Opportunity Index (UOI) is random or statistically clustered.

## 1. Rationale
* **First Law of Geography:** "Everything is related to everything else, but near things are more related than distant things" (Tobler, 1970).
* **Testing for Inequality:** If low-opportunity wards are clustered together, it indicates a "spatial trap" or systemic disadvantage in that region, rather than isolated cases of poor service.

## 2. Methodology
### A. Spatial Weights Matrix (Queen's Contiguity)
* We define "neighbors" using **Queen's Contiguity** (Wards sharing a boundary or a single point).
* The weights are **row-standardized** to account for wards having different numbers of neighbors.

### B. Global Moran's I
* **Null Hypothesis (H0):** The UOI scores are randomly distributed across Vadodara.
* **Test:** A Monte Carlo permutation test (999 simulations) is run to establish significance (p-value < 0.05).
* **Interpretation:**
    * **I > 0:** Positive Autocorrelation (High scores near High scores).
    * **I < 0:** Negative Autocorrelation (Checkerboard pattern).

### C. Local Moran's I (LISA)
* Decomposes the global statistic to identify specific "Hotspots" and "Coldspots."
* **Cluster Types:**
    1.  **High-High (HH):** A privileged ward surrounded by other privileged wards (e.g., Core City).
    2.  **Low-Low (LL):** A deprived ward surrounded by other deprived wards (The "Service Desert").
    3.  **High-Low / Low-High:** Spatial outliers.

## 3. Outputs
* **Maps:**
    * `moran_scatterplot.png`: Visual proof of slope.
    * `lisa_cluster_map.png`: The final map showing "Red Zones" (Deprived Clusters).