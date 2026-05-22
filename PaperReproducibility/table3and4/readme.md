# Case 2 Reproduction Guide: Tables 3 and 4

## Case 2. Raster-based co-seismic landslide example

This case uses raster-based spatial data to evaluate the geographic controls on co-seismic landslides. The dependent variable is landslide density, and the candidate explanatory factors include river density, elevation, road density, PGA, vegetation cover, fault density, aspect, and slope.

Tables 3 and 4 report the single-factor and stepwise multi-factor Geodetector results for this case.

---

## Required files

The following files should be stored in the `case/case2/` folder:

```text
case/case2/
│
├─ StepwiseGeodetector.py
├─ input.txt
├─ readme.md
│
├─ input/
│  ├─ LSD.tif
│  ├─ PGA.tif
│  ├─ DEM.tif
│  ├─ ASP.tif
│  ├─ SLP.tif
│  ├─ FAULT.tif
│  ├─ HYD.tif
│  ├─ LRD.tif
│  └─ VEG.tif
│
└─ output/
```

All paths should be relative to the `case/case2/` folder.

---

## Input raster layers

The input raster layers are stored in:

```text
case/case2/input/
```

The required raster files are:

| File | Role | Description |
|---|---|---|
| `LSD.tif` | Dependent variable | Landslide-density raster |
| `HYD.tif` | Candidate factor | River-density classes |
| `DEM.tif` | Candidate factor | Elevation classes |
| `LRD.tif` | Candidate factor | Road-density classes |
| `PGA.tif` | Candidate factor | Peak ground acceleration classes |
| `VEG.tif` | Candidate factor | Vegetation-cover classes |
| `FAULT.tif` | Candidate factor | Fault-density classes |
| `ASP.tif` | Candidate factor | Aspect classes |
| `SLP.tif` | Candidate factor | Slope-gradient classes |

All raster layers should have the same projection, extent, cell size, number of rows and columns, and grid alignment. In this case study, the target spatial resolution is 2000 m.

---

## Data preprocessing summary

Before running the Stepwise Geodetector analysis, all datasets were converted into a common 2000 m grid.

### Raster variables

PGA, elevation, aspect, and slope-gradient rasters were resampled to 2000 m using bilinear interpolation and then reclassified into categorical classes.

| Factor | Output raster | Resampling method | Cell size | Breakpoints |
|---|---|---|---:|---|
| PGA | `input/PGA.tif` | Bilinear | 2000 m | 0.110, 0.145, 0.180, 0.220 |
| Elevation | `input/DEM.tif` | Bilinear | 2000 m | 2350, 3200, 4020, 5100 |
| Aspect | `input/ASP.tif` | Bilinear | 2000 m | 45, 135, 225, 315 |
| Slope gradient | `input/SLP.tif` | Bilinear | 2000 m | 18.7, 30.4, 40.3, 52.2 |

### Point and line variables

Landslide points, road lines, fault lines, and river lines were converted into density rasters using kernel density estimation.

| Factor | Output raster | Method | Cell size | Search radius | Breakpoints |
|---|---|---|---:|---:|---|
| Landslide | `input/LSD.tif` | Kernel Density | 2000 m | 10000 m | Used as dependent variable |
| Road density | `input/LRD.tif` | Kernel Density | 2000 m | 10000 m | 0.032, 0.083, 0.137, 0.217 |
| Fault density | `input/FAULT.tif` | Kernel Density | 2000 m | 10000 m | 0.032, 0.078, 0.123, 0.175 |
| River density | `input/HYD.tif` | Kernel Density | 2000 m | 10000 m | 0.156, 0.282, 0.363, 0.431 |

Other kernel density parameters were kept as the default settings of the GIS software.

### Polygon variable

The vegetation polygon layer was converted or resampled to a 2000 m categorical raster.

| Factor | Output raster | Method | Cell size | Coding rule |
|---|---|---|---:|---|
| Vegetation cover | `input/VEG.tif` | Polygon to raster or resampling | 2000 m | Non-vegetated areas were coded as 0 |

---

## Configuration file

The raster-based program uses the text configuration file:

```text
case/case2/input.txt
```

A typical configuration is:

```text
input_folder: input
output_folder: output
value_raster: LSD.tif
factor_rasters: HYD.tif, DEM.tif, LRD.tif, PGA.tif, VEG.tif, FAULT.tif, ASP.tif, SLP.tif
lambda: 1
p_threshold: 0.05
min_group_size: 1
```

The exact keywords should match the format required by `StepwiseGeodetector.py`.

All paths should remain relative paths. The script should read raster data from:

```text
input/
```

and save results to:

```text
output/
```

---

## Reproduction command

Run the following command from the `case/case2/` folder:

```bash
python StepwiseGeodetector.py input.txt
```

The source code should not be modified.

---

## Output files

After running the script, the following output files will be generated in the output folder:

```text
output/all_candidate_results.csv
output/selected_path.csv
output/result.txt
output/step*_...__INTERSECT__*.tif
```

The main files used to reproduce Tables 3 and 4 are:

| Output file | Use |
|---|---|
| `output/all_candidate_results.csv` | Candidate single-factor and interaction results |
| `output/selected_path.csv` | Retained stepwise factor sequence |
| `output/result.txt` | Text summary of the selection process |
| `output/step*_...__INTERSECT__*.tif` | Generated interaction raster layers |

---

# Table 3. Single-factor q statistics for the landslide case

## Purpose

Table 3 reports the single-factor Geodetector results for the landslide case. It shows the explanatory power of each individual factor for the spatial distribution of landslide density.

The table reports:

- `Factor`: candidate explanatory factor;
- `q statistic`: single-factor explanatory power;
- `Decision`: whether the factor is selected as the initial factor.

---

## How to reproduce Table 3

Open the following output file:

```text
output/all_candidate_results.csv
```

Extract only the single-factor records for:

```text
HYD
DEM
LRD
PGA
VEG
FAULT
ASP
SLP
```

These correspond to the manuscript factor names:

| Raster name | Manuscript factor name |
|---|---|
| `HYD.tif` | River |
| `DEM.tif` | Elevation |
| `LRD.tif` | Road |
| `PGA.tif` | PGA |
| `VEG.tif` | Vegetation cover |
| `FAULT.tif` | Fault |
| `ASP.tif` | Aspect |
| `SLP.tif` | Slope |

Use the following columns to construct Table 3:

```text
Factor
q statistic
Decision
```

The factor with the largest single-factor q value is selected as the initial factor for the stepwise interaction analysis.

---

## Expected Table 3 results

| Factor | q statistic | Decision |
|---|---:|---|
| River | 0.248 | Selected as the initial factor |
| Elevation | 0.166 | Not selected |
| Road | 0.135 | Not selected |
| PGA | 0.120 | Not selected |
| Vegetation cover | 0.102 | Not selected |
| Fault | 0.083 | Not selected |
| Aspect | 0.006 | Not selected |
| Slope | 0.004 | Not selected |

Small numerical differences may occur because of rounding.

---

## Interpretation of Table 3

River has the highest single-factor q statistic and is therefore selected as the initial factor. Elevation, road density, PGA, vegetation cover, and fault density have moderate or weak explanatory power, while aspect and slope have very low individual q values.

The results indicate that river-related conditions provide the strongest individual explanation for the spatial variation of co-seismic landslides in this case.

---

# Table 4. Stepwise selection path for the landslide case

## Purpose

Table 4 reports the stepwise multi-factor selection path for the landslide case. Starting from the initial factor selected in Table 3, the program sequentially adds candidate factors and evaluates whether each added factor improves the explanatory power while maintaining an acceptable stratification structure.

The table reports:

- `Step`: stepwise selection step;
- `Retained combination`: factor combination retained at each step;
- `Added factor`: factor added at the current step;
- `q`: updated Geodetector q statistic;
- `Delta q`: increase in q compared with the previous retained step;
- `VR`: variance ratio;
- `S`: incremental selection score;
- `Reject`: whether the candidate combination is rejected.

---

## How to reproduce Table 4

Open the following output files:

```text
output/selected_path.csv
output/all_candidate_results.csv
output/result.txt
```

Use `selected_path.csv` to obtain the retained stepwise sequence.

Use `all_candidate_results.csv` to check the candidate results at each step.

Use `result.txt` to confirm the final retained combination and the rejected factor.

The retained and rejected combinations should be reported in the same order as the stepwise selection process.

---

## Expected Table 4 results

| Step | Retained combination | Added factor | q | Delta q | VR | S | Reject |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | River | — | 0.25 | — | 35.82 | — | No |
| 2 | River ∩ PGA | PGA | 0.53 | 0.28 | 20.47 | 0.84 | No |
| 3 | River ∩ PGA ∩ Fault | Fault | 0.72 | 0.19 | 10.88 | 0.82 | No |
| 4 | River ∩ PGA ∩ Fault ∩ Aspect | Aspect | 0.83 | 0.11 | 5.35 | 0.82 | No |
| 5 | River ∩ PGA ∩ Fault ∩ Aspect ∩ Slope | Slope | 0.94 | 0.11 | 3.47 | 0.54 | No |
| 6 | River ∩ PGA ∩ Fault ∩ Aspect ∩ Slope ∩ Elevation | Elevation | 0.98 | 0.04 | 5.96 | -0.50 | Yes |

Small numerical differences may occur because of rounding.

---

## Stepwise interpretation

At Step 1, River is selected as the initial factor because it has the highest single-factor q statistic.

At Step 2, PGA is added to River. This increases q from 0.25 to 0.53. Although VR decreases from 35.82 to 20.47, the incremental selection score remains positive, indicating that PGA provides additional explanatory information.

At Step 3, Fault is added. The q statistic increases to 0.72, and S remains positive.

At Step 4, Aspect is added. Although aspect has very weak individual explanatory power, it contributes conditional information when combined with river, PGA, and fault.

At Step 5, Slope is added. The q statistic increases to 0.94, and the positive S value indicates that the added factor is retained.

At Step 6, Elevation is tested. Although q increases from 0.94 to 0.98, VR increases from 3.47 to 5.96 and S becomes negative. Therefore, elevation is rejected, and the final retained combination is:

```text
River ∩ PGA ∩ Fault ∩ Aspect ∩ Slope
```

---

## Calculation formulas

The Geodetector q statistic is calculated as:

```text
q = 1 - SSW / SST
```

where:

```text
SSW = within-stratum sum of squares
SST = total sum of squares
```

The variance ratio is calculated as:

```text
VR = (SSB / (k - 1)) / (SSW / (n - k))
```

where:

```text
SSB = between-stratum sum of squares
SSW = within-stratum sum of squares
n   = number of valid samples
k   = number of valid groups
```

For stepwise interaction analysis, the incremental explanatory gain is:

```text
Delta q = q_new - q_previous
```

The incremental selection score is:

```text
S = Delta q - lambda * ln(VR_new / VR_previous)
```

where `lambda` controls the penalty assigned to the change in variance-ratio structure.

In this case, the value of `lambda` is:

```text
lambda = 1
```

---

## Notes for reproducibility

1. The source code should not be modified to reproduce Tables 3 and 4.
2. If the input folder, output folder, or raster file names are changed, only `input.txt` should be updated.
3. All input and output paths should remain relative paths.
4. Table 3 should be reproduced from the single-factor records in `output/all_candidate_results.csv`.
5. Table 4 should be reproduced from `output/selected_path.csv`, with candidate values checked against `output/all_candidate_results.csv` and `output/result.txt`.
6. Raster layers must be aligned before running the program.
7. Factor rasters should be categorical integer rasters.
8. Cells with NoData or invalid values should be excluded from the calculation.
9. Reviewers should be able to reproduce both tables by running the provided command without modifying the source code.

---

## Minimal reproduction summary

Run:

```bash
cd case/case2
python StepwiseGeodetector.py input.txt
```

Then use:

```text
output/all_candidate_results.csv
output/selected_path.csv
output/result.txt
```

to reproduce Tables 3 and 4.
