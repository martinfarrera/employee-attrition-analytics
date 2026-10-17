# Employee attrition analytics

Source intake (ODD **T1**, **S1/S2**) and a small descriptive EDA slice (**T2**, **S2/S4/S5**): deterministic validation, aggregate tables, a static visualization, and an [evidence-based report](reports/attrition-eda.md). The documented source has **16.12% Attrition = Yes**. No raw data is redistributed. Modeling and a demo remain future work.

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

## Intake contract and limits

The contract requires the commonly distributed 1,470-row, 35-column IBM HR CSV: exact ordered header, unique positive EmployeeNumber, no missing/padded values, known categorical values, nonnegative integer numeric fields, selected rating/constant bounds, and both attrition labels. The downloaded source passed the contract: 1,470 rows, 35 columns, 1,233 `No`, and 237 `Yes`. Source drift fails closed for review rather than being silently cleaned. Tests generate fictional rows and exercise the actual CLI.

A passing check establishes structural compatibility, not authenticity, license clearance, analytical validity, or causal meaning. SHA-256 records local bytes; there is no independently verified upstream digest yet. Re-running acquisition can yield a newer source version. Preserve a local receipt and digest to reproduce the exact input, rather than treating the live dataset slug as immutable.

This is an educational project using data described by the source as fictional. Its descriptive findings do not establish causation and must not support individual employment decisions.

## Observed access and remaining work

- `kaggle --version` reports `Kaggle API 1.7.4.5`.
- `kaggle datasets files` lists `WA_Fn-UseC_-HR-Employee-Attrition.csv` (227,977 bytes).
- Kaggle API metadata names the dataset, describes it as fictional data created by IBM data scientists, and reports `DbCL-1.0` for contents. See the [DbCL](https://opendatacommons.org/licenses/dbcl/1-0/) and incorporated [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) terms.
- Dataset access and metadata retrieval succeeded. Local download and validation passed on 2026-10-16 UTC. The file's exact-byte SHA-256 is recorded in the ignored local `data/raw/source-receipt.md`.

A public produced work must include a notice such as: “Contains information from [IBM HR Analytics Employee Attrition & Performance](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset), made available under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/); contents are licensed under [DbCL 1.0](https://opendatacommons.org/licenses/dbcl/1-0/).” No raw dataset is committed. No credential files or tokens were inspected, printed, or changed. The published intake slice does not include this local EDA work. Further publication is pending authorization; modeling and demo work are not implemented.
