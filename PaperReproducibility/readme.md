# Overall Data and Reproducibility Description

## Overview

This repository provides the data, codes, configuration files, and reproduction instructions for the manuscript on the Stepwise Geodetector framework. The purpose of the repository is to support research reproducibility by allowing users and reviewers to reproduce each reported figure, table, and metric using the shared data and scripts.

The repository contains three case studies:

1. **Case 1: Synthetic one-dimensional dataset**
2. **Case 2: Landslide dataset**
3. **Case 3: Disease dataset**

Each case folder includes the required input data, source code, configuration files, and reproduction instructions. All scripts use relative paths so that the repository can be moved or downloaded without modifying the source code.

---

## Repository structure

```text
StepwiseGeodetector/
│
├─ README.md
│
├─ case/
│  ├─ case1/
│  │  ├─ StepwiseGeodetector_with_config.py
│  │  ├─ config.json
│  │  ├─ synthetic_stepwise_geodetector_groups_123.xlsx
│  │  └─ readme.md
│  │
│  ├─ case2/
│  │  ├─ data/
│  │  ├─ input/
│  │  ├─ output/
│  │  ├─ StepwiseGeodetector.py
│  │  ├─ input.txt
│  │  ├─ violinplot_config.json
│  │  ├─ violinplot_params_config.py
│  │  └─ readme.md
│  │
│  └─ case3/
│     ├─ GeoDetector_2018_Example(Disease Dataset)_test.xlsm
│     ├─ StepwiseGeodetector_with_config.py
│     ├─ config.json
│     └─ readme.md
```

---

## Case 1: Synthetic one-dimensional dataset

Case 1 is a simple synthetic example used to demonstrate the basic behavior of the Geodetector `q` statistic, the variance ratio (`VR`), and the stepwise interaction procedure.

The input data are stored in:

```text
case/case1/synthetic_stepwise_geodetector_groups_123.xlsx
```

The dataset contains one response variable, `Y`, and three grouping variables, `X1`, `X2`, and `X3`.

Case 1 is used to reproduce:

| Manuscript item | Type | Description |
|---|---|---|
| Table 1 | Calculated result | Single-factor q and VR values for `X1`, `X2`, and `X3` |
| Table 2 | Calculated result | Stepwise interaction results for `X1 ∩ X2`, `X1 ∩ X3`, and `X1 ∩ X2 ∩ X3` |

The results are generated using:

```text
case/case1/StepwiseGeodetector_with_config.py
case/case1/config.json
```

---

## Case 2: Landslide dataset

Case 2 is the landslide dataset. It is used to demonstrate the application of the Stepwise Geodetector framework to a raster-based co-seismic landslide analysis.

The original landslide-related spatial data are stored in:

```text
case/case2/data/
```

The preprocessed and aligned raster layers used for calculation are stored in:

```text
case/case2/input/
```

The main raster inputs include:

```text
LSD.tif
PGA.tif
DEM.tif
ASP.tif
SLP.tif
FAULT.tif
HYD.tif
LRD.tif
VEG.tif
```

In this case, `LSD.tif` is the landslide-density raster and is used as the dependent variable. The other rasters are categorical explanatory factors.

Case 2 is used to reproduce:

| Manuscript item | Type | Description |
|---|---|---|
| Figure 2 | Original data visualization | Spatial distributions of landslides and candidate factors |
| Figure 3 | Calculated result | Violin plots of landslide density across factor classes |
| Table 3 | Calculated result | Single-factor q statistics for the landslide dataset |
| Table 4 | Calculated result | Stepwise multi-factor selection path for the landslide dataset |

Figure 2 is based on the original landslide-related spatial data. Figure 3 and Tables 3–4 are calculated results generated from the preprocessed raster layers.

The Stepwise Geodetector results are generated using:

```text
case/case2/StepwiseGeodetector.py
case/case2/input.txt
```

The violin plots for Figure 3 are generated using:

```text
case/case2/violinplot_params_config.py
case/case2/violinplot_config.json
```

---

## Case 3: Disease dataset

Case 3 uses the GeoDetector 2018 disease example dataset to demonstrate the Stepwise Geodetector workflow for disease prevalence analysis.

The input data are stored in:

```text
case/case3/GeoDetector_2018_Example(Disease Dataset)_test.xlsm
```

The dataset contains one dependent variable and three explanatory factors:

| Field | Role | Description |
|---|---|---|
| `incidence` | Dependent variable | Disease incidence or NTD prevalence |
| `type` | Candidate factor | Soil type |
| `region` | Candidate factor | Watershed region |
| `level` | Candidate factor | Elevation level |

Case 3 is used to reproduce:

| Manuscript item | Type | Description |
|---|---|---|
| Figure 4 | Original data visualization | Spatial distribution of disease incidence |
| Figure 5 | Original data visualization | Spatial distributions of disease-related candidate factors |
| Table 5 | Calculated result | Single-factor q and VR values |
| Table 6 | Calculated result | Step 2 two-factor interaction results |
| Table 7 | Calculated result | Step 3 three-factor interaction result |

Figures 4 and 5 are based on the original disease dataset. Tables 5–7 are calculated results generated by the Stepwise Geodetector program.

The results are generated using:

```text
case/case3/StepwiseGeodetector_with_config.py
case/case3/config.json
```

---

## Original data and calculated results

The manuscript includes both original data visualizations and calculated analytical results.

| Manuscript item | Case | Type | Description |
|---|---|---|---|
| Figure 2 | Case 2 | Original data visualization | Landslide-related spatial factors |
| Figure 3 | Case 2 | Calculated result | Violin plots based on landslide-density sampling |
| Figure 4 | Case 3 | Original data visualization | Disease incidence distribution |
| Figure 5 | Case 3 | Original data visualization | Disease-related factor distributions |
| Table 1 | Case 1 | Calculated result | Single-factor q and VR values |
| Table 2 | Case 1 | Calculated result | Stepwise interaction values |
| Table 3 | Case 2 | Calculated result | Landslide single-factor q statistics |
| Table 4 | Case 2 | Calculated result | Landslide stepwise selection path |
| Table 5 | Case 3 | Calculated result | Disease single-factor q and VR values |
| Table 6 | Case 3 | Calculated result | Disease two-factor interaction results |
| Table 7 | Case 3 | Calculated result | Disease three-factor interaction result |

---

## Reproducibility principle

The repository is organized to allow reviewers and users to reproduce the reported results without modifying the source code.

The general workflow is:

1. Open the corresponding case folder.
2. Check the input data and configuration file.
3. Run the provided command.
4. Use the generated output files to reproduce the reported figures, tables, and metrics.

All input and output paths are relative paths. If file names or folder names are changed, only the corresponding configuration file should be updated.

---

## Main output files

For the Excel-based cases, the main output files are:

```text
all_candidate_results.csv
selected_path.csv
result.txt
data_with_stepwise_groups.csv
data_with_stepwise_groups.xlsx
```

For the raster-based landslide case, the main output files are:

```text
all_candidate_results.csv
selected_path.csv
result.txt
step*_...__INTERSECT__*.tif
```

These output files provide the values used to reproduce the reported `q`, `VR`, `Delta q`, `S`, p-values, selected factor combinations, and rejection decisions.

---

## Notes

1. All scripts should be run without modifying the source code.
2. All paths should remain relative paths.
3. Each case folder contains a separate `readme.md` file with detailed reproduction instructions.
4. Figures 2, 4, and 5 are original data visualizations.
5. Figure 3 and Tables 1–7 are calculated analytical results.
6. The calculated tables should be reproduced from the output files generated by the scripts.
