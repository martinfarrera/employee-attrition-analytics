# Employee attrition analytics

Source intake (ODD **T1**, **S1/S2**) and a small descriptive EDA slice (**T2**, **S2/S4/S5**): deterministic validation, aggregate tables, a static visualization, and an [evidence-based report](reports/attrition-eda.md). The documented source has **16.12% Attrition = Yes**. No raw data is redistributed. An educational model comparison (**T3**, **S2/S4**) adds held-out evaluation; a demo remains future work.

## Quick path

Run from this project directory with Python 3.10+:

```sh
python -m pytest -q -p no:cacheprovider
python -B src/intake.py plan --terms-reviewed
```

The plan command only prints acquisition commands; without `--terms-reviewed` it exits 2. See [source, license status, and acquisition instructions](data/raw/README.md). `requirements.txt` pins test/optional acquisition tooling; the validator itself has no third-party dependencies. No installer was run for this slice.

After acquisition:

```sh
python -B src/intake.py validate data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv
```

Success exits 0 and prints sorted JSON with source identifier, row/column counts, attrition counts, and the exact input-byte SHA-256. Failure exits 1, prints a diagnostic to stderr, and emits no success report. `validate -` also accepts CSV bytes on stdin. Validation never contacts Kaggle, rewrites input, or prints employee rows.

## Reproduce the exploratory analysis

```sh
python -B src/eda.py data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv --output reports
```

The dependency-free command reuses intake validation and writes only two global
aggregate CSV tables, an accessible SVG, and `reports/attrition-eda.md`. It exits 0
with a one-line summary; input or write errors exit 1 with stderr diagnostics.
Invalid input creates no output and leaves existing reports unchanged. Successful
runs replace these four named artifacts deterministically. Filesystem write errors
can leave partial output; rerun after correcting the destination. Use a dedicated
output directory, not a directory containing source data.

The checked-in artifacts use the aggregate counts already recorded in T1 (not a
fresh inspection of raw data). Tests reproduce those exact artifacts with generated
fictional rows having the same label totals, and check CLI errors and repeatability.
This first EDA slice covers overall distribution and class imbalance only; subgroup
exploration is deferred. The majority-label accuracy of 83.88% is descriptive,
not evaluated predictive performance. See the report for limitations and attribution.

## Reproduce the educational model comparison

Use a dedicated output directory **outside `reports/`**: the EDA regression tests
compare all checked-in reports recursively. No model artifacts are checked in.

```sh
python -B src/model.py data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv --output /tmp/attrition-model
python -m pytest -q -p no:cacheprovider tests/test_model.py
```

The standard-library CLI validates the complete input with `intake.validate` before
writing anything. It writes only `model.json`: aggregate class counts, fitted rule,
held-out confusion counts and metrics, source SHA-256, algorithm version, and
limitations. It never exports employee-level predictions. Success exits 0 with
train/test sizes; input or filesystem errors exit 1 with a stderr diagnostic;
argument usage errors exit 2. `--help` describes the command without reading data.

Successful reruns overwrite `model.json` deterministically for identical input
bytes and runtime. Other destination files remain unchanged. Invalid input leaves
existing output untouched and creates no output. Filesystem failures can leave
partial output; correct the destination and rerun. Do not use source storage as
output: source-containing directories and source aliases at the target are rejected.
The command requires at least five examples of each class.

### What is being compared?

| Choice | Contract (`decision-stump-v1`) |
| --- | --- |
| Holdout | Seed 42; shuffle each class in input order (`No`, then `Yes`); reserve `floor(class size / 5)` examples per class for testing. Record train/test class counts. |
| Baseline | Predict the training-majority label for every held-out example. Label ties predict `No`. |
| Classifier | A single numeric threshold with training-majority labels in its two leaves; left means value <= threshold. A constant fallback is allowed. |
| Features | In tie-breaking order: `YearsAtCompany`, `TrainingTimesLastYear`, `JobSatisfaction`, `WorkLifeBalance`. These offer a small, understandable work-context feature set. |
| Training | Search boundaries between distinct observed training values; use the lower observed value as threshold. Maximize training balanced accuracy. Equal scores retain the constant fallback, then the first feature/ascending threshold. Leaf ties predict `No`. |
| Evaluation | Test rows are used only after fitting. Report `Yes` precision, recall, F1, overall accuracy, balanced accuracy (mean sensitivity/specificity), and `tn/fp/fn/tp`. Undefined precision/F1 is reported as zero. |

Identifiers, demographic fields, compensation, other work variables, and the target
are excluded from predictors. There is no scaling, imputation, external dependency,
or test-set tuning. Excluding demographics does **not** eliminate proxy bias.
The source digest identifies exact local bytes, not authenticity; preserve those
bytes and the algorithm/runtime version when reproducing a run.

A high overall accuracy can merely reflect class imbalance. Read positive-class
recall and balanced accuracy alongside the baseline, not accuracy alone. A single
holdout on fictional data offers no uncertainty estimate, temporal validation,
external validation, or fairness audit. Threshold search can overfit training data;
the model is deliberately limited and may not improve on the baseline. These are
educational associations, not causal findings or tools for individual employment
decisions.

### Observed local-source result

Verification of the locally validated source used **1,177 training
rows** (`No`: 987, `Yes`: 190) and **293 test rows** (`No`: 246, `Yes`: 47).
The fitted stump retained the constant `No` fallback: **no improvement over the
baseline**. Both produced TN 246, FP 0, FN 47, TP 0; accuracy **83.96%**, balanced
accuracy **0.50**, and `Yes` precision, recall, and F1 **0**. The apparently high
accuracy reflects imbalance, not useful minority-class detection: neither model
identified any held-out attrition cases. This negative result does not justify
employment use or further tuning against the same held-out data. The generated
aggregate artifact records the exact input SHA-256; it is not checked in.

## Intake contract and limits

The contract requires the commonly distributed 1,470-row, 35-column IBM HR CSV: exact ordered header, unique positive EmployeeNumber, no missing/padded values, known categorical values, nonnegative integer numeric fields, selected rating/constant bounds, and both attrition labels. The downloaded source passed the contract: 1,470 rows, 35 columns, 1,233 `No`, and 237 `Yes`. Source drift fails closed for review rather than being silently cleaned. Tests generate fictional rows and exercise the actual CLI.

A passing check establishes structural compatibility, not authenticity, license clearance, analytical validity, or causal meaning. SHA-256 records local bytes; there is no independently verified upstream digest yet. Re-running acquisition can yield a newer source version. Preserve a local receipt and digest to reproduce the exact input, rather than treating the live dataset slug as immutable.

This is an educational project using data described by the source as fictional. Its descriptive findings do not establish causation and must not support individual employment decisions.

## Observed access and remaining work

- `kaggle --version` reports `Kaggle API 1.7.4.5`.
- `kaggle datasets files` lists `WA_Fn-UseC_-HR-Employee-Attrition.csv` (227,977 bytes).
- Kaggle API metadata names the dataset, describes it as fictional data created by IBM data scientists, and reports `DbCL-1.0` for contents. See the [DbCL](https://opendatacommons.org/licenses/dbcl/1-0/) and incorporated [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) terms.
- Dataset access and metadata retrieval succeeded. Local download and validation passed on 2026-10-16 UTC. The file's exact-byte SHA-256 is recorded in the ignored local `data/raw/source-receipt.md`.

A public produced work must include a notice such as: “Contains information from [IBM HR Analytics Employee Attrition & Performance](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset), made available under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/); contents are licensed under [DbCL 1.0](https://opendatacommons.org/licenses/dbcl/1-0/).” No raw dataset is committed. No credential files or tokens were inspected, printed, or changed. The intake and EDA slices are published through commit `6c33c15`. The model comparison adds the reproducible evaluation documented above; the demo is not implemented.
