# Case 3 Reproduction Guide: Tables 5, 6, and 7

## Case 3. Disease dataset example

This case uses the GeoDetector 2018 disease example dataset to demonstrate the Stepwise Geodetector workflow for disease prevalence analysis. The dependent variable is disease incidence, and the candidate explanatory factors include soil type, watershed region, and elevation.

Tables 5, 6, and 7 report the single-factor and stepwise multi-factor interaction results for this case.

---

## Required files

The following files should be stored in the `case/case3/` folder:

```text
case/case3/
│
├─ GeoDetector_2018_Example(Disease Dataset)_test.xlsm
├─ StepwiseGeodetector_with_config.py
├─ config.json
└─ readme.md
```

All paths should be relative to the `case/case3/` folder.

---

## Input data

The input Excel workbook is:

```text
GeoDetector_2018_Example(Disease Dataset)_test.xlsm
```

The dataset contains the dependent variable and three candidate explanatory factors.

| Field | Role | Description |
|---|---|---|
| `incidence` | Dependent variable | Disease incidence or NTD prevalence |
| `type` | Candidate factor | Soil type |
| `region` | Candidate factor | Watershed region |
| `level` | Candidate factor | Elevation level |

The Excel workbook should contain at least the following columns:

```text
incidence
type
region
level
```

If the file name is changed by the operating system, the `input_excel` field in `config.json` should be updated accordingly.

---

## Configuration file

Use the following configuration file:

```text
case/case3/config.json
```

The content of `config.json` should be:

```json
{
  "input_excel": "GeoDetector_2018_Example(Disease Dataset)_test.xlsm",
  "output_folder": "disease_example_stepwise_output",
  "value_col": "incidence",
  "factor_cols": ["type", "region", "level"],
  "lam": 1,
  "p_threshold": 0.05,
  "min_group_size": 1,
  "verbose": true
}
```

All paths are relative to the `case/case3/` folder.

---

## Reproduction command

Run the following command from the `case/case3/` folder:

```bash
python StepwiseGeodetector_with_config.py --config config.json
```

The source code should not be modified.

---

## Output files

After running the script, the following output folder will be generated:

```text
disease_example_stepwise_output/
```

The main output files are:

```text
disease_example_stepwise_output/all_candidate_results.csv
disease_example_stepwise_output/selected_path.csv
disease_example_stepwise_output/result.txt
disease_example_stepwise_output/data_with_stepwise_groups.csv
disease_example_stepwise_output/data_with_stepwise_groups.xlsx
```

The main files used to reproduce Tables 5, 6, and 7 are:

| Output file | Use |
|---|---|
| `all_candidate_results.csv` | Single-factor and candidate interaction results |
| `selected_path.csv` | Retained stepwise factor sequence |
| `result.txt` | Text summary of the selection process |
| `data_with_stepwise_groups.csv` | Input data with generated stepwise group labels |
| `data_with_stepwise_groups.xlsx` | Excel version of grouped output data |

---

# Table 5. Step 1: q statistics and variance ratios for single factors

## Purpose

Table 5 reports the single-factor Geodetector results for the disease dataset. It evaluates the explanatory power and variance-ratio structure of each individual factor.

The table reports:

- `q`: Geodetector q statistic;
- `VR`: variance ratio;
- candidate factors: soil type, watershed region, and elevation.

---

## How to reproduce Table 5

Open the following output file:

```text
disease_example_stepwise_output/all_candidate_results.csv
```

Extract only the single-factor records for:

```text
type
region
level
```

These correspond to the manuscript factor names:

| Field name | Manuscript factor name |
|---|---|
| `type` | Soil Type |
| `region` | Watershed Region |
| `level` | Elevation |

Use the following values to construct Table 5:

```text
q
VR
```

Do not use interaction records for Table 5. Interaction records are used for Tables 6 and 7.

---

## Expected Table 5 results

| Statistic | Soil Type | Watershed Region | Elevation |
|---|---:|---:|---:|
| q | 0.39 | 0.64 | 0.61 |
| VR | 28.26 | 38.74 | 45.77 |

More detailed output values may be approximately:

| Factor | q | VR | p-value | k |
|---|---:|---:|---:|---:|
| Soil Type | 0.385717 | 28.256119 | 3.20641e-18 | 5 |
| Watershed Region | 0.637774 | 38.735508 | 4.97855e-35 | 9 |
| Elevation | 0.606709 | 45.765125 | 1.30030e-33 | 7 |

Small numerical differences may occur because of rounding.

---

## Interpretation of Table 5

Watershed region has the highest single-factor q statistic and is therefore selected as the initial factor for the stepwise interaction analysis. Elevation has a slightly lower q statistic but the highest VR value. Soil type has a lower q value than watershed region and elevation.

Following the stepwise selection rule, the initial factor is selected primarily according to the highest q statistic, while VR is used as an auxiliary diagnostic of stratification structure.

---

# Table 6. Step 2: Interaction q and VR values for candidate two-factor combinations

## Purpose

Table 6 reports the Step 2 candidate interaction results. After watershed region is selected as the initial factor, the remaining two factors, soil type and elevation, are separately intersected with watershed region.

The table compares:

```text
Watershed Region ∩ Soil Type
Watershed Region ∩ Elevation
```

The table reports:

- `q`: updated Geodetector q statistic;
- `VR`: variance ratio;
- `S`: incremental selection score.

---

## How to reproduce Table 6

Open the following output file:

```text
disease_example_stepwise_output/all_candidate_results.csv
```

Extract the Step 2 interaction records for:

```text
region ∩ type
region ∩ level
```

These correspond to the manuscript names:

| Field combination | Manuscript combination |
|---|---|
| `region ∩ type` | Watershed Region ∩ Soil Type |
| `region ∩ level` | Watershed Region ∩ Elevation |

Use the following columns to construct Table 6:

```text
q
VR
S
```

Use `selected_path.csv` and `result.txt` to confirm which Step 2 interaction was retained.

---

## Expected Table 6 results

| Statistic | Watershed Region ∩ Soil Type | Watershed Region ∩ Elevation |
|---|---:|---:|
| q | 0.74 | 0.71 |
| VR | 22.82 | 18.35 |
| S | 0.63 | 0.82 |

More detailed output values may be approximately:

| Combination | q | VR | S |
|---|---:|---:|---:|
| Watershed Region ∩ Soil Type | 0.735681 | 22.82 | 0.626892 |
| Watershed Region ∩ Elevation | 0.71 | 18.35 | 0.82 |

Small numerical differences may occur because of rounding.

---

## Step 2 decision rule

The Stepwise Geodetector procedure first identifies the candidate with the highest updated q value. The incremental selection score `S` is then used to determine whether the improvement is acceptable.

At Step 2:

```text
Watershed Region ∩ Soil Type
```

has the higher q value and a positive S value. Therefore, soil type is selected as the second factor.

Although:

```text
Watershed Region ∩ Elevation
```

has a larger S value, it has a lower updated q value. Therefore, it is not selected at Step 2.

---

# Table 7. Step 3: q, VR, and S values for the three-factor interaction

## Purpose

Table 7 reports the Step 3 three-factor interaction result. After watershed region and soil type are retained, elevation is added to form the three-factor interaction.

The table reports:

- `q`: updated Geodetector q statistic;
- `VR`: variance ratio;
- `S`: incremental selection score.

---

## How to reproduce Table 7

Open the following output files:

```text
disease_example_stepwise_output/selected_path.csv
disease_example_stepwise_output/all_candidate_results.csv
disease_example_stepwise_output/result.txt
```

Extract the Step 3 retained interaction:

```text
region ∩ type ∩ level
```

This corresponds to the manuscript combination:

```text
Watershed Region ∩ Soil Type ∩ Elevation
```

Use the following columns to construct Table 7:

```text
q
VR
S
```

---

## Expected Table 7 results

| Statistic | Watershed Region ∩ Soil Type ∩ Elevation |
|---|---:|
| q | 0.80 |
| VR | 14.13 |
| S | 0.541 |

More detailed output values may be approximately:

| Combination | q | VR | S |
|---|---:|---:|---:|
| Watershed Region ∩ Soil Type ∩ Elevation | 0.797000 | 14.13 | 0.540510 |

Small numerical differences may occur because of rounding.

---

## Step 3 interpretation

At Step 3, elevation is added to the retained combination:

```text
Watershed Region ∩ Soil Type
```

The resulting three-factor interaction is:

```text
Watershed Region ∩ Soil Type ∩ Elevation
```

This interaction increases q to approximately 0.80, reduces VR to approximately 14.13, and produces a positive S value. Therefore, the three-factor interaction is retained as the final selected combination.

The final retained factor combination is:

```text
Watershed Region ∩ Soil Type ∩ Elevation
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

1. The source code should not be modified to reproduce Tables 5, 6, and 7.
2. If the input file name or output folder name is changed, only `config.json` should be updated.
3. All input and output paths should remain relative paths.
4. Table 5 should be reproduced from the single-factor records in `all_candidate_results.csv`.
5. Table 6 should be reproduced from the Step 2 interaction records in `all_candidate_results.csv`.
6. Table 7 should be reproduced from the Step 3 retained interaction record in `selected_path.csv` or `result.txt`.
7. The retained stepwise path should be checked using both `selected_path.csv` and `result.txt`.
8. Reviewers should be able to reproduce all three tables by running the provided command without modifying the source code.

---

## Minimal reproduction summary

Run:

```bash
cd case/case3
python StepwiseGeodetector_with_config.py --config config.json
```

Then use:

```text
disease_example_stepwise_output/all_candidate_results.csv
disease_example_stepwise_output/selected_path.csv
disease_example_stepwise_output/result.txt
```

to reproduce Tables 5, 6, and 7.
