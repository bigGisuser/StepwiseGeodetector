# Case 3

## 1. Purpose

This guide explains how to run the **Stepwise GeoDetector** program using the disease dataset example from the GeoDetector 2018 sample data.

The program reads an Excel workbook, calculates GeoDetector statistics for each candidate factor and their stepwise interactions, and outputs the retained factor sequence.

The disease example uses:

```text
Dependent variable: incidence
Candidate factors: type, region, level
```

The current case is controlled by a JSON configuration file and is intended to be run with:

```bash
python StepwiseGeodetector_with_config.py --config config.json
```

---

## 2. Required Files

Place the following files in the same working folder:

```text
StepwiseGeodetector_with_config.py
config.json
GeoDetector_2018_Example(Disease Dataset)_test.xlsm
```

Recommended folder structure:

```text
project_folder/
│
├─ StepwiseGeodetector_with_config.py
├─ config.json
├─ GeoDetector_2018_Example(Disease Dataset)_test.xlsm
│
└─ disease_example_stepwise_output/
   ├─ all_candidate_results.csv
   ├─ selected_path.csv
   ├─ result.txt
   ├─ data_with_stepwise_groups.csv
   └─ data_with_stepwise_groups.xlsx
```

> Note: If the uploaded Excel file is automatically renamed by the system, for example as `GeoDetector_2018_Example(Disease Dataset)_test(1).xlsm`, either rename it to `GeoDetector_2018_Example(Disease Dataset)_test.xlsm` or update the `input_excel` field in `config.json`.

---

## 3. Input Excel File

The Excel file should contain one worksheet with the following columns:

| Column | Role | Description |
|---|---|---|
| `incidence` | Dependent variable Y | Disease incidence value used as the response variable |
| `type` | Candidate factor | Categorical explanatory factor |
| `region` | Candidate factor | Categorical regional grouping factor |
| `level` | Candidate factor | Categorical level or class factor |

Each candidate factor must be a categorical variable. The category labels may be numbers such as `1`, `2`, `3`, etc. They are treated as group labels, not as continuous numeric values.

The current dataset contains 185 records and four columns:

```text
incidence, type, region, level
```

---

## 4. Configuration File

The current `config.json` should be written as:

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

Parameter meanings:

| Parameter | Meaning |
|---|---|
| `input_excel` | Name or path of the input Excel file |
| `output_folder` | Folder where the result files will be saved |
| `value_col` | Dependent variable column, here `incidence` |
| `factor_cols` | Candidate explanatory factors, here `type`, `region`, and `level` |
| `lam` | Penalty coefficient λ used in the S statistic |
| `p_threshold` | Significance threshold for retaining candidate factors |
| `min_group_size` | Minimum sample size required for each stratum |
| `verbose` | Whether to print detailed running information in the terminal |

### Path rule

Relative paths in `config.json` are interpreted relative to the folder containing the configuration file. For example, if `config.json` and the Excel file are in the same folder, this is valid:

```json
"input_excel": "GeoDetector_2018_Example(Disease Dataset)_test.xlsm"
```

The output folder:

```json
"output_folder": "disease_example_stepwise_output"
```

will be created inside the same folder as `config.json`.

---

## 5. Install Required Python Packages

Install the required packages before running the script:

```bash
pip install pandas numpy scipy openpyxl xlrd
```

Package roles:

| Package | Use |
|---|---|
| `pandas` | Read Excel files and process tables |
| `numpy` | Numerical calculation |
| `scipy` | F-test p-value calculation |
| `openpyxl` | Read `.xlsx` and `.xlsm` files |
| `xlrd` | Read older `.xls` files if needed |

---

## 6. Run the Program

Open a terminal in the project folder and run:

```bash
python StepwiseGeodetector_with_config.py --config config.json
```

If your configuration file uses a different name, for example `config_disease_example.json`, run:

```bash
python StepwiseGeodetector_with_config.py --config config_disease_example.json
```

When `verbose` is set to `true`, the terminal will print the loaded configuration, single-factor screening results, candidate interaction results, and the final selected combination.

---

## 7. Output Files

After running the program, the following files will be generated in:

```text
disease_example_stepwise_output/
```

| Output file | Description |
|---|---|
| `all_candidate_results.csv` | Results for all single factors and all candidate interaction combinations |
| `selected_path.csv` | Final retained stepwise factor sequence |
| `result.txt` | Human-readable summary of the analysis |
| `data_with_stepwise_groups.csv` | Original data plus selected stepwise grouping columns |
| `data_with_stepwise_groups.xlsx` | Excel version of the grouped output |

The grouped output files contain extra columns such as:

```text
__step1_selected_group
__step2_selected_group
__step3_selected_group
```

These columns record the retained grouping structure at each accepted step.

---

## 8. Calculation Formulas

For each factor or factor combination, the program calculates the GeoDetector q statistic:

```text
q = 1 - SSW / SST
```

where:

| Symbol | Meaning |
|---|---|
| `SST` | Total sum of squares of the dependent variable |
| `SSW` | Within-stratum sum of squares |
| `SSB` | Between-stratum sum of squares, calculated as `SST - SSW` |
| `n` | Number of valid samples |
| `k` | Number of valid strata |

The variance ratio is calculated as:

```text
VR = (SSB / (k - 1)) / (SSW / (n - k))
```

For Step 2 and later, the incremental selection score is:

```text
S = Δq - λ ln(VR_new / VR_previous)
```

where:

```text
Δq = q_new - q_previous
```

---

## 9. Stepwise Selection Rule

The program uses a two-stage selection logic.

### Step 1: single-factor screening

The script calculates `q`, `VR`, and `p` for each single factor:

```text
type
region
level
```

The initial factor is selected as the statistically significant factor with the largest `q`.

### Step 2 and later: interaction screening

For each remaining factor, the script creates an interaction between the current selected combination and the candidate factor. For example, after `region` is selected, the script evaluates:

```text
region ∩ type
region ∩ level
```

The candidate with the largest `q` is selected first. Then `S > 0` is used as the retention criterion.

A new factor is retained only when:

```text
Δq > 0
p <= p_threshold
S > 0
```

Important: `S` is not used to rank candidates. The candidate is ranked by `q`; `S` is used to decide whether the maximum-q candidate should be retained.

---

## 10. Expected Results for This Disease Dataset Case

Using the current configuration:

```text
λ = 1
p_threshold = 0.05
min_group_size = 1
```

The expected single-factor results are approximately:

| Factor | q | VR | p-value | k |
|---|---:|---:|---:|---:|
| `type` | 0.385717 | 28.256119 | 3.20641e-18 | 5 |
| `region` | 0.637774 | 38.735508 | 4.97855e-35 | 9 |
| `level` | 0.606709 | 45.765125 | 1.30030e-33 | 7 |

Therefore, `region` is selected as the initial factor because it has the largest single-factor q value.

The expected stepwise path is:

| Step | Retained combination | Added factor | q | S | Decision |
|---:|---|---|---:|---:|---|
| 1 | `region` | `region` | 0.637774 | — | Retained as initial factor |
| 2 | `region ∩ type` | `type` | 0.735681 | 0.626892 | Retained |
| 3 | `region ∩ type ∩ level` | `level` | 0.797000 | 0.540510 | Retained |

The final retained combination is:

```text
region ∩ type ∩ level
```

This means that `region` provides the strongest single-factor explanation of disease incidence, `type` adds further explanatory refinement, and `level` provides an additional positive contribution under the current λ and p-value settings.

---

## 11. How to Read the Output Tables

### `selected_path.csv`

Use this file to check the final retained factor sequence.

Important columns:

| Column | Meaning |
|---|---|
| `step` | Step number in the selection process |
| `candidate_factor` | Factor added at this step |
| `combination` | Current retained factor combination |
| `q` | Explanatory power of the current combination |
| `delta_q` | Increase in q compared with the previous retained step |
| `vr` | Variance ratio of the current combination |
| `vr_ratio` | Ratio between current VR and previous VR |
| `s` | Incremental selection score |
| `p` | Significance value |
| `retained` | Whether the factor was retained |
| `reason` | Reason for selection or rejection |

### `all_candidate_results.csv`

Use this file to inspect all tested candidates, including candidates that were not retained.

For this disease dataset case, Step 2 compares:

```text
region ∩ type
region ∩ level
```

Although `region ∩ level` has a positive S value, `region ∩ type` has the larger q value, so `type` is retained at Step 2.

---

## 12. Common Problems and Solutions

### Problem 1: The Excel file cannot be found

Check whether the filename in `config.json` exactly matches the actual Excel filename.

For example, this config expects:

```text
GeoDetector_2018_Example(Disease Dataset)_test.xlsm
```

If your file is named:

```text
GeoDetector_2018_Example(Disease Dataset)_test(1).xlsm
```

then either rename the Excel file or change `input_excel` in `config.json`.

### Problem 2: Column names do not exist

Check that the Excel file contains the exact column names:

```text
incidence
type
region
level
```

Column names are case-sensitive after cleaning spaces.

### Problem 3: `openpyxl` is missing

For `.xlsm` files, install `openpyxl`:

```bash
pip install openpyxl
```

### Problem 4: `k < 2`

This means that a factor has fewer than two valid strata after filtering. Check whether the factor column contains valid class labels.

### Problem 5: `n <= k`

This means the number of interaction strata is too large relative to the number of valid samples. Reduce the number of classes, merge sparse strata, or increase the sample size.

---

## 13. Suggested Reporting Text

The following sentence can be used when reporting this example:

```text
For the disease dataset example, the stepwise GeoDetector first selected region as the initial factor because it had the largest single-factor q value. In the subsequent interaction analysis, type was retained at Step 2 and level was retained at Step 3 because both increased q and satisfied the S > 0 retention criterion. The final retained combination was region ∩ type ∩ level.
```
