# Case 1 Reproduction Guide: Tables 1 and 2

## Case 1. Synthetic one-dimensional example

This case uses a simple one-dimensional synthetic dataset to demonstrate how different grouping schemes affect the Geodetector `q` statistic, the variance ratio (`VR`), and the stepwise interaction results.

---

## Required files

The following files should be stored in the `case/case1/` folder:

```text
case/case1/
│
├─ StepwiseGeodetector_with_config.py
├─ config.json
├─ readme.md
└─ synthetic_stepwise_geodetector_groups_123.xlsx
```

All paths are relative to the `case/case1/` folder.

---

## Input data

The response variable is:

```text
Y = [8.00, 8.00, 8.03, 8.05, 8.20, 8.22, 8.23, 8.25, 9.00, 9.10, 9.20, 9.30, 9.40, 9.50]
```

Three grouping schemes are used:

```text
X1: [8.00–8.25] = 1, [9.00–9.50] = 2
X2: [8.00–8.05] = 1, [8.20–9.50] = 2
X3: [8.00–9.40] = 1, [9.50] = 2
```

The input Excel file is:

```text
synthetic_stepwise_geodetector_groups_123.xlsx
```

The Excel file should contain at least the following columns:

```text
Y
X1
X2
X3
```

---

## Configuration file

Use the following `config.json` file:

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

All paths are relative to the `case/case1/` folder.

---

## Reproduction command

Run the following command from the `case/case1/` folder:

```bash
python StepwiseGeodetector_with_config.py --config config.json
```

After running the script, the following output folder will be generated:

```text
synthetic_stepwise_output_config/
```

The main output files are:

```text
synthetic_stepwise_output_config/all_candidate_results.csv
synthetic_stepwise_output_config/selected_path.csv
synthetic_stepwise_output_config/result.txt
synthetic_stepwise_output_config/data_with_stepwise_groups.csv
synthetic_stepwise_output_config/data_with_stepwise_groups.xlsx
```

---

# Table 1. q and VR values for alternative single-factor segmentation schemes

## Purpose

Table 1 reports the single-factor Geodetector results for the synthetic example. It shows how the three alternative grouping schemes, `X1`, `X2`, and `X3`, explain the variance of the response variable `Y`.

The table reports:

- `Group`: grouping scheme;
- `k`: number of valid groups;
- `q`: Geodetector q statistic;
- `VR`: variance ratio.

---

## How to reproduce Table 1

Open the following output file:

```text
synthetic_stepwise_output_config/all_candidate_results.csv
```

Extract only the single-factor records for:

```text
X1
X2
X3
```

Use the following columns to construct Table 1:

```text
Group
k
q
VR
```

Do not use interaction records for Table 1. Interaction records such as `X1 ∩ X2`, `X1 ∩ X3`, and `X1 ∩ X2 ∩ X3` are used for Table 2.

---

## Expected Table 1 results

| Group | k | q | VR |
|---|---:|---:|---:|
| X1 | 2 | 0.9433 | 199.52 |
| X2 | 2 | 0.4158 | 8.54 |
| X3 | 2 | 0.1864 | 2.75 |

Small numerical differences may occur because of rounding.

---

## Interpretation of Table 1

Among the three grouping schemes, `X1` has the largest `q` statistic and the largest `VR` value. This indicates that `X1` provides the strongest single-factor explanation of the variance structure in the synthetic response variable.

Therefore, `X1` is selected as the initial factor for the subsequent stepwise interaction analysis.

The results also show that finer or more imbalanced grouping schemes do not necessarily improve explanatory power. In this example, the broad separation represented by `X1` captures the dominant variance structure more effectively than `X2` or `X3`.

---

# Table 2. q and VR values for stepwise interaction stratifications

## Purpose

Table 2 reports the stepwise interaction results for Case 1. After `X1` is selected as the initial factor, the remaining factors are sequentially intersected with `X1` to evaluate whether additional grouping factors improve the explanatory power.

The table reports:

- `Group`: interaction combination;
- `k`: number of valid groups;
- `q`: Geodetector q statistic;
- `VR`: variance ratio.

---

## How to reproduce Table 2

Open the following output files:

```text
synthetic_stepwise_output_config/all_candidate_results.csv
synthetic_stepwise_output_config/selected_path.csv
synthetic_stepwise_output_config/result.txt
```

Use `all_candidate_results.csv` to obtain the candidate interaction results.

Extract the records for:

```text
X1 ∩ X2
X1 ∩ X3
X1 ∩ X2 ∩ X3
```

Use the following columns to construct Table 2:

```text
Group
k
q
VR
```

Use `selected_path.csv` and `result.txt` to confirm the retained stepwise path.

---

## Expected Table 2 results

| Group | k | q | VR |
|---|---:|---:|---:|
| X1 ∩ X2 | 3 | 0.9615 | 137.2 |
| X1 ∩ X3 | 3 | 0.9595 | 130.3 |
| X1 ∩ X2 ∩ X3 | 4 | 0.9777 | 146.1 |

Small numerical differences may occur because of rounding.

---

## Stepwise interpretation

At Step 1, `X1` is selected as the initial factor because it has the largest single-factor `q` value.

At Step 2, the two candidate interactions are compared:

```text
X1 ∩ X2
X1 ∩ X3
```

Both interactions increase `q` compared with `X1` alone, but `X1 ∩ X2` has the slightly higher `q` value. Therefore, `X1 ∩ X2` is retained as the preferred two-factor combination.

At Step 3, `X3` is added to the retained combination to form:

```text
X1 ∩ X2 ∩ X3
```

This three-factor interaction further increases `q`, but it also changes the variance-ratio structure. Whether this additional refinement should be retained depends on the incremental selection score `S` and the selected value of `lambda`.

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

---

## Notes for reproducibility

1. The source code should not be modified to reproduce Tables 1 and 2.
2. If the input file name or output folder name is changed, only `config.json` should be updated.
3. All input and output paths should remain relative paths.
4. Table 1 should be reproduced from the single-factor records in `all_candidate_results.csv`.
5. Table 2 should be reproduced from the interaction records in `all_candidate_results.csv`.
6. The retained stepwise path should be checked using `selected_path.csv` and `result.txt`.
7. Reviewers should be able to reproduce both tables by running the provided command without modifying the source code.

---

## Minimal reproduction summary

Run:

```bash
cd case/case1
python StepwiseGeodetector_with_config.py --config config.json
```

Then use:

```text
synthetic_stepwise_output_config/all_candidate_results.csv
```

to reproduce Tables 1 and 2.
