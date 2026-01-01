# Modeling Urban Inequality in Vadodara

### A Geospatial & Network-Based Analysis

**Ethan Hunt**  
Master’s Student — Statistics  
The Maharaja Sayajirao University of Baroda

Note:
Introduce yourself and the motivation briefly.
---
## Motivation

- Urban inequality is unevenly distributed
- City-level averages mask local deprivation
- Infrastructure is experienced spatially

**Core idea:** Access, not availability, defines opportunity.
---
## Research Questions

- Is access to services spatially equitable?
- Do deprived wards form persistent clusters?
- How does network-based accessibility differ from Euclidean distance?
- Can opportunity be measured objectively?
---
## Conceptual Framework

- City as a **road network**
- Opportunity measured via **travel time**
- Inequality tested using **spatial statistics**
--
### Analytical Layers

1. Network modeling  
2. Accessibility computation  
3. Spatial dependence analysis
---
## Data

- 19 administrative wards (post-2011)
- OpenStreetMap road network
- Hospitals, schools, transport nodes
--
### Network Scale

- ~50,000 nodes  
- ~120,000 edges  
- Travel-time weighted
---
## Methodology: Accessibility

- Graph-based city representation
- Shortest-path algorithms
- Travel-time based access

**Why not Euclidean distance?**  
Cities are navigated, not flown over.
---
## Urban Opportunity Index (UOI)

- Standardized indicators
- PCA-based aggregation
- Objective, variance-driven weights
--
### Why PCA?

- Avoids arbitrary weighting
- Captures multidimensional access
- Statistically interpretable
---
## Spatial Validation

- Global Moran’s I
- Local Moran’s I (LISA)

Tests whether inequality is random or structured.
--
### LISA Identifies

- High–High clusters (privilege)
- Low–Low clusters (deprivation)
- Spatial outliers
---
## Key Findings

- Inequality is spatially structured
- Western wards show opportunity clusters
- Central wards show deprivation traps
- Transport connectivity is critical
---
## Maps & Visuals

- Urban Opportunity Index map
- LISA cluster map
- Moran’s I scatterplot

*(Maps shown during presentation)*
---
## Policy Implications

1. Targeted ward-level intervention
2. Transport as an equity lever
3. Spatial diagnostics over city averages
---
## Phase 2: Validation

- Stratified household survey
- High / Medium / Low UOI wards
- ~200 households
--
### Objective

Compare modeled accessibility with lived experience.
---
## Conclusion

- Urban inequality is spatially entrenched
- Networks shape opportunity
- Spatial statistics reveal hidden structure

**Cities are not just built — they are experienced.**
---
## Thank You

Questions?
