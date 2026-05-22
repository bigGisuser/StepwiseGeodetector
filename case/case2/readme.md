# Case 2

This guide explains how to run the current `StepwiseGeodetector.py` script using the provided `input.txt` configuration file.

The current workflow is designed for raster-based Stepwise GeoDetector analysis. It evaluates single factors first, then progressively tests interaction combinations between the selected factor set and the remaining candidate factors.

---

## 1. Required Files

Place the following files in the same project folder:

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
```

Therefore, the script will look for all raster files in the `input` folder relative to the folder that contains `input.txt`.

---

## 2. Required Raster Data

| File | Role | Description |
|---|---|---|
| `LSD.tif` | Dependent variable raster | Response variable used as `Y`, such as landslide density or landslide occurrence |
| `PGA.tif` | Candidate factor | Peak ground acceleration classes |
| `LRD.tif` | Candidate factor | Landslide-related density or road-density classes |
| `VEG.tif` | Candidate factor | Vegetation classes, for example generated from the `GB` attribute field |
| `ASP.tif` | Candidate factor | Aspect classes |
| `DEM.tif` | Candidate factor | Elevation classes |
| `FAULT.tif` | Candidate factor | Fault density classes |
| `HYD.tif` | Candidate factor | River or hydrological density classes |
| `SLP.tif` | Candidate factor | Slope gradient classes |

All rasters must have the same:

- projection;
- extent;
- cell size;
- number of rows and columns;
- grid alignment.

The factor rasters must be categorical rasters with integer class labels, such as:

```text
1, 2, 3, 4, 5
```

Invalid cells should be coded as `0` or NoData. In this script, `0` in factor rasters is treated as invalid during GeoDetector calculation and raster intersection.

---

## 3. Input Configuration File

The current `input.txt` is:

```text
input_folder: input

value_file: LSD.tif

factor_files:
PGA.tif
LRD.tif
VEG.tif
ASP.tif
DEM.tif
FAULT.tif
HYD.tif
SLP.tif

output_folder: output

lambda: 1

p_threshold: 0.05

min_group_size: 1
```

### 3.1 Configuration keys

| Key | Meaning |
|---|---|
| `input_folder` | Folder containing the dependent variable raster and all factor rasters |
| `value_file` | Dependent variable raster used as `Y` |
| `factor_files` | Candidate factor raster list; write one raster file name per line |
| `output_folder` | Folder for output files; if it is a relative path, it is created inside `input_folder` |
| `lambda` | Penalty coefficient used in the `S` statistic |
| `p_threshold` | Significance threshold used for candidate filtering |
| `min_group_size` | Kept for compatibility and reporting; single-sample strata are not removed in the current version |

### 3.2 Path rule

The script resolves relative paths as follows:

1. `input_folder` is resolved relative to the folder containing `input.txt`.
2. `value_file` and all `factor_files` are resolved relative to `input_folder`.
3. `output_folder` is also resolved relative to `input_folder`.

For the current configuration:

```text
input_folder: input
output_folder: output
```

The actual output folder will be:

```text
project_folder/input/output/
```

If you want the output folder to be outside the raster input folder, use a relative path such as:

```text
output_folder: ../output
```

This will save results to:

```text
project_folder/output/
```

---

## 4. Run the Program

Open a terminal in the project folder and run:

```bash
python StepwiseGeodetector.py input.txt
```

You can also run the script without specifying `input.txt` if `input.txt` is in the same folder as `StepwiseGeodetector.py`:

```bash
python StepwiseGeodetector.py
```

In that case, the script automatically uses:

```text
input.txt
```

from the script folder.

---

## 5. Main Calculation Procedure

The script performs the following steps.

### Step 1: Single-factor screening

Each candidate factor is evaluated separately. The script calculates:

```text
q, VR, p, n, k, SSW, SSB, SST, minimum group size, maximum group size
```

The initial factor is selected by the following rule:

1. Among statistically significant factors, select the factor with the maximum `q` value.
2. If no factor is statistically significant, still select the factor with the maximum `q` value and record this situation in the `reason` field.

### Step 2 and later: Stepwise interaction evaluation

For each remaining factor, the script intersects the current selected raster combination with the candidate factor raster. The interaction strata are relabeled from `1` to `k`, while invalid cells are coded as `0`.

For each candidate interaction, the script calculates:

```text
Delta q = q_new - q_previous
VR ratio = VR_new / VR_previous
S = Delta q - lambda * ln(VR_new / VR_previous)
```

At each step, the script applies the following selection rule:

1. Keep candidates with `Delta q > 0` and `p <= p_threshold`.
2. Select the candidate with the maximum updated `q` value from this pool.
3. Retain this maximum-`q` candidate only if `S > 0`.

If the maximum-`q` candidate has `S <= 0`, the stepwise process stops and no new factor is retained.

---

## 6. Output Files

The current configuration saves results in:

```text
project_folder/input/output/
```

Main output files are:

| Output file | Description |
|---|---|
| `all_candidate_results.csv` | Results for all single factors and all tested interaction candidates |
| `selected_path.csv` | Final selected factor sequence |
| `result.txt` | Human-readable text summary of the selected path and all candidate results |
| `step*_...__INTERSECT__*.tif` | Generated interaction raster layers |

---

## 7. Meaning of Important Output Columns

| Column | Meaning |
|---|---|
| `step` | Step number in the stepwise process |
| `candidate_factor` | Candidate factor tested at the current step |
| `combination` | Factor combination represented by the candidate interaction |
| `q` | GeoDetector explanatory power |
| `delta_q` | Increase in `q` after adding the candidate factor |
| `vr` | Variance ratio, equivalent to an F-type statistic in this implementation |
| `vr_ratio` | Relative change in VR compared with the previous selected combination |
| `s` | Incremental selection score |
| `p` | p-value calculated from the F distribution |
| `n` | Number of valid raster cells used in the calculation |
| `k` | Number of valid strata |
| `min_group_size` | Minimum number of cells in a stratum |
| `max_group_size` | Maximum number of cells in a stratum |
| `accepted` | Whether the candidate was retained in the final selected path |
| `reason` | Reason for selection, rejection, or stopping |
| `raster_path` | Path to the original or generated raster used for this calculation |

---

## 8. Interpretation of `q`, `VR`, and `S`

### `q`

The `q` statistic measures the explanatory power of a factor or factor combination:

```text
q = 1 - SSW / SST
```

A larger `q` value indicates stronger explanatory power.

### `VR`

The variance ratio is calculated as:

```text
VR = (SSB / (k - 1)) / (SSW / (n - k))
```

where:

- `SST` is the total sum of squares of the dependent variable;
- `SSW` is the within-strata sum of squares;
- `SSB` is the between-strata sum of squares;
- `n` is the number of valid samples;
- `k` is the number of valid strata.

### `S`

The `S` statistic evaluates whether the explanatory gain is large enough relative to the change in VR:

```text
S = Delta q - lambda * ln(VR_new / VR_previous)
```

A candidate is retained only when:

```text
S > 0
```

A larger `lambda` applies a stronger penalty to increases in VR. A smaller `lambda` gives more weight to explanatory gain measured by `Delta q`.

---

## 9. Common Problems and Solutions

### Raster cannot be opened

Check whether the raster file is located in the folder defined by `input_folder`.

For the current configuration, the following path must exist:

```text
project_folder/input/LSD.tif
```

and all factor rasters must also be located in:

```text
project_folder/input/
```

### Raster size mismatch

The script checks whether the dependent variable raster and factor rasters have the same row and column dimensions. If a mismatch occurs, make sure all rasters have the same extent, resolution, and grid alignment.

### The number of valid strata is less than 2

This means that a factor raster has fewer than two valid classes after NoData and zero cells are removed. Check the raster reclassification result.

### Cannot calculate VR/F because `n <= k`

This means the interaction produced too many strata relative to the number of valid samples. Reduce the number of classes or merge small classes before running the analysis again.

### Output folder is not where expected

Remember that `output_folder` is resolved relative to `input_folder`. With:

```text
input_folder: input
output_folder: output
```

outputs are saved to:

```text
project_folder/input/output/
```

To save outputs to `project_folder/output/`, use:

```text
output_folder: ../output
```

---

## 10. Recommended Workflow

1. Prepare all raster layers and ensure they have the same projection, extent, resolution, and grid alignment.
2. Reclassify each candidate factor raster into integer classes.
3. Save all raster files in the `input` folder.
4. Check and edit `input.txt`.
5. Run:

```bash
python StepwiseGeodetector.py input.txt
```

6. Check the output files:

```text
input/output/all_candidate_results.csv
input/output/selected_path.csv
input/output/result.txt
```

7. Use `selected_path.csv` and `result.txt` to report the final selected factor sequence.

---

## 11. Notes

- The script uses `0` as invalid cells for categorical factor rasters.
- Single-sample strata are not removed in the current version.
- The current selection rule uses maximum `q` for candidate selection and uses `S > 0` only as a retention condition.
- The output interaction rasters are automatically generated and saved as GeoTIFF files.
- Use relative paths in `input.txt` to make the project easier to move or share.
