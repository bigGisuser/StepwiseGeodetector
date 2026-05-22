# Reproduction Guide for Figures and Tables

This guide explains how to reproduce the figures and tables reported in the manuscript. The workflow is organized into three case studies:

- **Case 1:** synthetic one-dimensional Excel example;
- **Case 2:** raster-based co-seismic landslide example;
- **Case 3:** disease dataset example from the GeoDetector 2018 sample data.

All paths are written as relative paths. This makes the project easier to move, share, and reproduce on different computers.

---

## 1. Overview of the Three Cases

| Case | Data type | Main script | Configuration file | Main output |
|---|---|---|---|---|
| Case 1 | Excel table | `StepwiseGeodetector_with_config.py` | `config.json` | Tables 1–2 |
| Case 2 | Raster data | `StepwiseGeodetector.py` | `input.txt` | Figure 2, Figure 3, Tables 3–4 |
| Case 3 | Excel workbook | `StepwiseGeodetector_with_config.py` | `config.json` | Figures 4–5, Tables 5–7 |

The two Excel-based cases use a JSON configuration file. The raster-based case uses a text configuration file named `input.txt`.

---

## 2. General Stepwise GeoDetector Selection Rule

The Stepwise GeoDetector workflow first evaluates each single factor and then progressively evaluates interaction combinations.

For each factor or factor combination, the program calculates:

```text
q = 1 - SSW / SST
```

and

```text
VR = (SSB / (k - 1)) / (SSW / (n - k))
```

where `SST` is the total sum of squares, `SSW` is the within-stratum sum of squares, `SSB` is the between-stratum sum of squares, `n` is the number of valid samples, and `k` is the number of valid strata.

For Step 2 and later, the incremental selection score is:

```text
S = Delta q - lambda * ln(VR_new / VR_previous)
```

where:

```text
Delta q = q_new - q_previous
```

The selection rule is:

1. **Step 1:** select the statistically significant single factor with the largest `q` value.
2. **Step 2 and later:** rank candidate interactions by the updated `q` value.
3. Retain the maximum-`q` candidate only when:

```text
Delta q > 0
p <= p_threshold
S > 0
```

Therefore, `S` is used as a retention and stopping criterion, not as the candidate-ranking criterion.

---

## 3. Case 1: Synthetic Excel Example

### 3.1 Purpose

Case 1 uses a simple one-dimensional synthetic dataset to show how different grouping schemes affect variance decomposition and stepwise factor selection.

The response variable is:

```text
Y = [8.00, 8.00, 8.03, 8.05, 8.20, 8.22, 8.23, 8.25, 9.00, 9.10, 9.20, 9.30, 9.40, 9.50]
```

The candidate grouping factors are:

```text
X1: [8.00–8.25] = 1, [9.00–9.50] = 2
X2: [8.00–8.05] = 1, [8.20–9.50] = 2
X3: [8.00–9.40] = 1, [9.50] = 2
```

### 3.2 Required files

```text
StepwiseGeodetector_with_config.py
config.json
synthetic_stepwise_geodetector_groups_123.xlsx
```

### 3.3 Configuration file

The example `config.json` is:

```json
{
  "input_excel": "synthetic_stepwise_geodetector_groups_123.xlsx",
  "output_folder": "synthetic_stepwise_output_config",
  "value_col": "Y",
  "factor_cols": ["X1", "X2", "X3"],
  "lam": 1,
  "p_threshold": 0.05,
  "min_group_size": 1,
  "verbose": true
}
```

Relative paths in `input_excel` and `output_folder` are interpreted relative to the folder containing `config.json`.

### 3.4 Reproduce Tables 1 and 2

Run:

```bash
python StepwiseGeodetector_with_config.py --config config.json
```

The main output files are:

```text
synthetic_stepwise_output_config/all_candidate_results.csv
synthetic_stepwise_output_config/selected_path.csv
synthetic_stepwise_output_config/result.txt
synthetic_stepwise_output_config/data_with_stepwise_groups.csv
synthetic_stepwise_output_config/data_with_stepwise_groups.xlsx
```

Table 1 can be extracted from the Step 1 single-factor records in `all_candidate_results.csv`.

Table 2 can be extracted from the interaction records in `all_candidate_results.csv`, `selected_path.csv`, and `result.txt`.

The expected retained path for this case is:

```text
Step 1: X1
Step 2: X1 ∩ X2
```

The candidate combination `X1 ∩ X2 ∩ X3` is expected to be rejected by the `S` criterion because the additional explanatory gain is not sufficient to offset the increase in variance-ratio structure.

---

## 4. Case 2: Raster-Based Co-Seismic Landslide Example

### 4.1 Purpose

Case 2 uses raster layers to evaluate the spatial controls of co-seismic landslides. The dependent variable is a landslide-related raster, and the explanatory factors are categorical raster layers.

### 4.2 Required folder structure

The recommended structure is:

```text
project_folder/
│
├─ StepwiseGeodetector.py
├─ input.txt
│
└─ input/
   ├─ LSD.tif
   ├─ PGA.tif
   ├─ LRD.tif
   ├─ VEG.tif
   ├─ ASP.tif
   ├─ DEM.tif
   ├─ FAULT.tif
   ├─ HYD.tif
   └─ SLP.tif
```

The provided `input.txt` uses:

```text
input_folder: input
output_folder: output
```

Therefore, the program reads raster files from:

```text
project_folder/input/
```

and saves output files to:

```text
project_folder/input/output/
```

To save outputs outside the raster input folder, use:

```text
output_folder: ../output
```

### 4.3 Required raster files

| File | Role | Description |
|---|---|---|
| `LSD.tif` | Dependent variable raster | Landslide density, landslide occurrence, or another landslide-related response variable |
| `PGA.tif` | Candidate factor | Peak ground acceleration classes |
| `LRD.tif` | Candidate factor | Landslide-related density or road-density classes |
| `VEG.tif` | Candidate factor | Vegetation classes |
| `ASP.tif` | Candidate factor | Aspect classes |
| `DEM.tif` | Candidate factor | Elevation classes |
| `FAULT.tif` | Candidate factor | Fault density classes |
| `HYD.tif` | Candidate factor | River or hydrological density classes |
| `SLP.tif` | Candidate factor | Slope gradient classes |

All rasters must have the same projection, extent, cell size, row number, column number, and grid alignment. In this case study, the raster resolution is 2000 m.

Factor rasters must be categorical rasters with integer class labels. Invalid cells should be coded as `0` or NoData. The script treats `0` in factor rasters as invalid.

### 4.4 Reproduce Figure 2

Figure 2 shows the spatial distributions of the candidate factors used in Case 2. It can be reproduced by displaying the preprocessed categorical factor rasters with the same map scale, projection, north orientation, and legend style.

The candidate factor rasters are:

```text
PGA.tif
LRD.tif
VEG.tif
ASP.tif
DEM.tif
FAULT.tif
HYD.tif
SLP.tif
```

Use one common map layout where possible to avoid duplicated legends, scale bars, and north arrows.

### 4.5 Reproduce Figure 3

Figure 3 shows the distribution of the dependent variable across the classes of each candidate factor. It is generated from:

- value raster: `LSD.tif`;
- label raster: one candidate factor raster, such as `VEG.tif`, `PGA.tif`, or `DEM.tif`.

An example command for vegetation is:

```bash
python violinplot_params.py ^
  --value-raster input/LSD.tif ^
  --label-raster input/VEG.tif ^
  --output input/output/figures/violin_VEG.png ^
  --x-label "Vegetation class" ^
  --y-label "Landslide density"
```

The same command can be repeated for the other factor rasters by changing `--label-raster`, `--output`, and `--x-label`.

### 4.6 Reproduce Tables 3 and 4

Run:

```bash
python StepwiseGeodetector.py input.txt
```

The main output files are:

```text
input/output/all_candidate_results.csv
input/output/selected_path.csv
input/output/result.txt
input/output/step*_...__INTERSECT__*.tif
```

Table 3 can be extracted from the single-factor results in `all_candidate_results.csv`.

Table 4 can be extracted from `selected_path.csv`, `all_candidate_results.csv`, and `result.txt`.

---

## 5. Case 3: Disease Dataset Example

### 5.1 Purpose

Case 3 uses the GeoDetector 2018 disease sample dataset to demonstrate the Stepwise GeoDetector workflow for disease incidence analysis.

The dataset uses:

```text
Dependent variable: incidence
Candidate factors: type, region, level
```

### 5.2 Required files

```text
StepwiseGeodetector_with_config.py
config.json
GeoDetector_2018_Example(Disease Dataset)_test.xlsm
```

If the Excel file is automatically renamed by the operating system, for example:

```text
GeoDetector_2018_Example(Disease Dataset)_test(1).xlsm
```

then either rename the file or update the `input_excel` field in `config.json`.

### 5.3 Configuration file

The current `config.json` is:

```json
{
  "input_excel": "GeoDetector_2018_Example(Disease Dataset)_test.xlsm",
  "output_folder": "disease_example_stepwise_output",
  "value_col": "incidence",
  "factor_cols": [
    "type",
    "region",
    "level"
  ],
  "lam": 1,
  "p_threshold": 0.05,
  "min_group_size": 1,
  "verbose": true
}
```

The output folder will be created as:

```text
disease_example_stepwise_output/
```

### 5.4 Reproduce Figures 4 and 5

Figure 4 shows the spatial distribution of disease incidence. The dependent variable is:

```text
incidence
```

Figure 5 shows the spatial or categorical distributions of the explanatory factors:

```text
type
region
level
```

These figures should be generated from the original disease dataset using the same classification and map layout used in the manuscript.

### 5.5 Reproduce Tables 5–7

Run:

```bash
python StepwiseGeodetector_with_config.py --config config.json
```

The main output files are:

```text
disease_example_stepwise_output/all_candidate_results.csv
disease_example_stepwise_output/selected_path.csv
disease_example_stepwise_output/result.txt
disease_example_stepwise_output/data_with_stepwise_groups.csv
disease_example_stepwise_output/data_with_stepwise_groups.xlsx
```

Table 5 can be extracted from the Step 1 single-factor records in `all_candidate_results.csv`.

Table 6 can be extracted from the Step 2 interaction records in `all_candidate_results.csv`.

Table 7 can be extracted from the Step 3 interaction record in `selected_path.csv` or `result.txt`.

The expected single-factor results are approximately:

| Factor | q | VR | p-value | k |
|---|---:|---:|---:|---:|
| `type` | 0.385717 | 28.256119 | 3.20641e-18 | 5 |
| `region` | 0.637774 | 38.735508 | 4.97855e-35 | 9 |
| `level` | 0.606709 | 45.765125 | 1.30030e-33 | 7 |

The expected retained path is:

| Step | Retained combination | Added factor | q | S | Decision |
|---:|---|---|---:|---:|---|
| 1 | `region` | `region` | 0.637774 | — | Retained as initial factor |
| 2 | `region ∩ type` | `type` | 0.735681 | 0.626892 | Retained |
| 3 | `region ∩ type ∩ level` | `level` | 0.797000 | 0.540510 | Retained |

The final retained combination is:

```text
region ∩ type ∩ level
```

---

## 6. Summary of Reproduction Commands

### Case 1: Synthetic Excel example

```bash
python StepwiseGeodetector_with_config.py --config config.json
```

### Case 2: Raster-based landslide example

```bash
python StepwiseGeodetector.py input.txt
```

### Case 2: Violin plots for Figure 3

```bash
python violinplot_params.py ^
  --value-raster input/LSD.tif ^
  --label-raster input/VEG.tif ^
  --output input/output/figures/violin_VEG.png ^
  --x-label "Vegetation class" ^
  --y-label "Landslide density"
```

### Case 3: Disease dataset example

```bash
python StepwiseGeodetector_with_config.py --config config.json
```

---

## 7. Output Files Used for Manuscript Tables

For all three cases, the numerical values used in the manuscript tables should be taken from:

```text
all_candidate_results.csv
selected_path.csv
result.txt
```

For Excel-based cases, the following grouped data files are also generated:

```text
data_with_stepwise_groups.csv
data_with_stepwise_groups.xlsx
```

For the raster-based case, the generated interaction rasters are saved as:

```text
step*_...__INTERSECT__*.tif
```

---
