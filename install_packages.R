# Script: install_packages.R
# Purpose: Install all R dependencies for the Vadodara Inequality Project

# 1. Install Package Manager if missing
if (!require("pacman")) install.packages("pacman")

# 2. List of required libraries
libs <- c(
  "tidyverse",  # Data manipulation (dplyr, readr, etc.)
  "sf",         # Spatial data handling (Simple Features)
  "here",       # Project-relative paths
  "psych",      # Principal Component Analysis (PCA)
  "knitr",      # Nice console tables
  "cli",        # Professional logging
  "spdep",      # Spatial Statistics (Moran's I)
  "tmap"        # Cartography and Mapping
  "pacman"      # for package management 
)

# 3. Install and Load
pacman::p_load(char = libs, install = TRUE, update = FALSE)

message("✅ All R packages installed successfully!")