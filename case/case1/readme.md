# Case 1

This repository provides a simple Excel-based implementation of a stepwise GeoDetector workflow. The program reads a table of a dependent variable and candidate grouping factors, calculates GeoDetector statistics, evaluates interaction combinations step by step, and exports the retained factor path and all candidate results.

The current version is designed to run with a JSON configuration file, so users do not need to edit the Python script directly.

---

## 1. Main Files

```text
StepwiseGeodetector_with_config.py
config.json
synthetic_stepwise_geodetector_groups_123.xlsx
```

| File | Purpose |
|---|---|
| `StepwiseGeodetector_with_config.py` | Main Python script for running the stepwise GeoDetector workflow |
| `config.json` | JSON configuration file defining input data, output folder, selected columns, and model parameters |
| `synthetic_stepwise_geodetector_groups_123.xlsx` | Example Excel input file |

If `config.json` does not exist, the script will automatically create a default template and stop. After checking or editing the generated configuration file, run the script again.

---

## 2. Example Input Data

The example uses a simple one-dimensional synthetic dataset:

```text
Y = [8.00, 8.00, 8.03, 8.05, 8.20, 8.22, 8.23, 8.25, 9.00, 9.10, 9.20, 9.30, 9.40, 9.50]
```

Three candidate grouping factors are used:

```text
X1: [8.00–8.25] = 1, [9.00–9.50] = 2
X2: [8.00–8.05] = 1, [8.20–9.50] = 2
X3: [8.00–9.40] = 1, [9.50] = 2
```

The Excel input file should contain one dependent variable column and one or more candidate factor columns. For the example dataset, the expected format is:

| Y | X1 | X2 | X3 |
|---:|---:|---:|---:|
| 8.00 | 1 | 1 | 1 |
| 8.00 | 1 | 1 | 1 |
| 8.03 | 1 | 1 | 1 |
| 8.05 | 1 | 1 | 1 |
| 8.20 | 1 | 2 | 1 |
| 8.22 | 1 | 2 | 1 |
| 8.23 | 1 | 2 | 1 |
| 8.25 | 1 | 2 | 1 |
| 9.00 | 2 | 2 | 1 |
| 9.10 | 2 | 2 | 1 |
| 9.20 | 2 | 2 | 1 |
| 9.30 | 2 | 2 | 1 |
| 9.40 | 2 | 2 | 1 |
| 9.50 | 2 | 2 | 2 |

`Y` is the dependent variable. `X1`, `X2`, and `X3` are candidate grouping factors. The values `1` and `2` are category labels, not numerical magnitudes.

---

## 3. Configuration File

The program is controlled by `config.json`.

Example:

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

| Parameter | Description |
|---|---|
| `input_excel` | Path to the input Excel file. Supported formats include `.xlsx`, `.xlsm`, and `.xls`. |
| `output_folder` | Folder used to save output files. It will be created automatically if it does not exist. |
| `value_col` | Name of the dependent variable column. If omitted, the first column is used. |
| `factor_cols` | List of candidate grouping factor columns. If omitted, all columns except `value_col` are used as factors. |
| `lam` | Penalty coefficient λ in the S statistic. |
| `p_threshold` | Significance threshold used in factor retention. |
| `min_group_size` | Minimum number of samples required in each stratum. Strata smaller than this value are removed before calculation. |
| `verbose` | If `true`, detailed running information is printed to the terminal. |

### Path rule

Relative paths in `input_excel` and `output_folder` are interpreted relative to the folder containing `config.json`, not necessarily the current terminal directory. This makes the workflow easier to run from different locations.

---

## 4. Installation

Install the required Python packages:

```bash
pip install pandas numpy scipy openpyxl xlrd
```

Notes:

- `openpyxl` is used for reading and writing `.xlsx` files.
- `xlrd` is required if the input file is an old `.xls` file.
- If `openpyxl` is missing, the program can still export CSV and text results, but the grouped `.xlsx` output may not be created.

---

## 5. How to Run

Put the Python script, configuration file, and Excel input file in the same folder:

```text
project_folder/
├─ StepwiseGeodetector_with_config.py
├─ config.json
└─ synthetic_stepwise_geodetector_groups_123.xlsx
```

Run:

```bash
python StepwiseGeodetector_with_config.py --config config.json
```

If the configuration file is named `config.json` and is located in the same folder as the Python script, you can also run:

```bash
python StepwiseGeodetector_with_config.py
```

---

## 6. Output Files

After the program finishes, the following files are saved in the output folder defined by `output_folder`:

```text
all_candidate_results.csv
selected_path.csv
result.txt
data_with_stepwise_groups.csv
data_with_stepwise_groups.xlsx
```

| Output file | Description |
|---|---|
| `all_candidate_results.csv` | Statistics for all single factors and all evaluated interaction candidates |
| `selected_path.csv` | Final retained stepwise factor path |
| `result.txt` | Human-readable summary of the configuration, selection rule, selected path, and candidate results |
| `data_with_stepwise_groups.csv` | Original data plus the retained grouping column for each selected step |
| `data_with_stepwise_groups.xlsx` | Excel version of `data_with_stepwise_groups.csv` |

---

## 7. Main Statistics

The program calculates the following GeoDetector statistics:

```text
q = 1 - SSW / SST
```

```text
VR = (SSB / (k - 1)) / (SSW / (n - k))
```

where:

| Symbol | Meaning |
|---|---|
| `SST` | Total sum of squares of the dependent variable |
| `SSW` | Within-stratum sum of squares |
| `SSB` | Between-stratum sum of squares |
| `n` | Number of valid samples |
| `k` | Number of valid strata |
| `q` | Explanatory power of a factor or factor combination |
| `VR` | Variance ratio / F statistic |
| `p` | p-value calculated from the F distribution |

The incremental selection score is:

```text
S = Δq - λ ln(VR_new / VR_previous)
```

where:

```text
Δq = q_new - q_previous
```

A larger `λ` applies a stronger penalty to increases in `VR`. A smaller `λ` gives more weight to the increase in explanatory power.

---

## 8. Stepwise Selection Rule

### Step 1: single-factor screening

The program calculates `q`, `VR`, and `p` for each single factor. The initial factor is selected as follows:

1. Among factors with `p <= p_threshold`, select the factor with the largest `q`.
2. If no factor is significant, select the factor with the largest `q` and record this situation in the output.

### Step 2 and later: interaction evaluation

For each remaining factor, the program generates an interaction group with the current retained factor combination.

For example, if the current retained factor is `X1`, the next candidates are:

```text
X1 ∩ X2
X1 ∩ X3
```

The program then:

1. Keeps candidates with `Δq > 0` and `p <= p_threshold`.
2. Selects the candidate with the largest `q` from this candidate pool.
3. Uses `S > 0` as the retention criterion.

A new factor is retained only if:

```text
Δq > 0
p <= p_threshold
S > 0
```

If the maximum-`q` candidate has `S <= 0`, it is rejected and the stepwise procedure stops.

Important: `S` is used as a retention and stopping criterion, not as the ranking criterion. Candidate ranking is based on `q`.

---

## 9. Expected Example Result

For the synthetic example, the expected retained path is:

```text
Step 1: X1
Step 2: X1 ∩ X2
```

The next candidate combination:

```text
X1 ∩ X2 ∩ X3
```

is expected to be rejected by the `S` criterion, because the additional explanatory gain is not sufficient to offset the increase in structural complexity.

The final retained combination is therefore:

```text
X1 ∩ X2
```

---

## 10. Common Problems

### Configuration file not found

If `config.json` is missing, the script creates a default configuration template and stops. Edit the generated file and run the script again.

### Column name does not exist

Check that `value_col` and all names in `factor_cols` exactly match the column names in the Excel file.

### `openpyxl` is missing

Install it with:

```bash
pip install openpyxl
```

Without `openpyxl`, the program may still generate CSV and text outputs, but `.xlsx` export may fail.

### Too few valid strata

Each factor or interaction group must contain at least two valid strata. If a factor has only one valid class after filtering by `min_group_size`, the calculation cannot be performed.

### `n <= k` error

This means that the number of valid samples is less than or equal to the number of strata. Reduce the number of classes, merge small groups, or lower `min_group_size` when appropriate.

---

## 11. Recommended Citation in a Manuscript or Report

When describing this workflow, you may write:

> A stepwise GeoDetector procedure was used to identify parsimonious factor combinations. At each step, candidate interactions were ranked by the q statistic, while the incremental score S was used as a retention criterion to balance explanatory gain against changes in variance-ratio structure.
