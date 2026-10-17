# Employee attrition analytics — source intake

First reviewable slice (ODD **T1**, **S1/S2**): a non-executing Kaggle acquisition plan and deterministic, offline CSV validation. A local dataset was downloaded and validated, but no raw data is redistributed. EDA, modeling, and demo are future work, not implemented here.

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

## Intake contract and limits

The contract requires the commonly distributed 1,470-row, 35-column IBM HR CSV: exact ordered header, unique positive EmployeeNumber, no missing/padded values, known categorical values, nonnegative integer numeric fields, selected rating/constant bounds, and both attrition labels. The downloaded source passed the contract: 1,470 rows, 35 columns, 1,233 `No`, and 237 `Yes`. Source drift fails closed for review rather than being silently cleaned. Tests generate fictional rows and exercise the actual CLI.

A passing check establishes structural compatibility, not authenticity, license clearance, analytical validity, or causal meaning. SHA-256 records local bytes; there is no independently verified upstream digest yet. Re-running acquisition can yield a newer source version. Preserve a local receipt and digest to reproduce the exact input, rather than treating the live dataset slug as immutable.

This is an educational project. Future analysis must verify the source's synthetic/fictional-data description and limitations, and must not support individual employment decisions.

## Observed access and remaining work

- `kaggle --version` reports `Kaggle API 1.7.4.5`.
- `kaggle datasets files` lists `WA_Fn-UseC_-HR-Employee-Attrition.csv` (227,977 bytes).
- Kaggle API metadata names the dataset, describes it as fictional data created by IBM data scientists, and reports `DbCL-1.0` for contents. See the [DbCL](https://opendatacommons.org/licenses/dbcl/1-0/) and incorporated [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) terms.
- Dataset access and metadata retrieval succeeded. Local download and validation passed on 2026-10-16 UTC. The file's exact-byte SHA-256 is recorded in the ignored local `data/raw/source-receipt.md`.

A public produced work must include a notice such as: “Contains information from [IBM HR Analytics Employee Attrition & Performance](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset), made available under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/); contents are licensed under [DbCL 1.0](https://opendatacommons.org/licenses/dbcl/1-0/).” No raw dataset is committed. No credential files or tokens were inspected, printed, or changed. Publication of this initial slice does not imply that EDA, modeling, or demo work is complete.
