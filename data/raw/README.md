# Source and acquisition notes

**Kaggle metadata reports `DbCL-1.0` for dataset contents.** The [Database Contents License](https://opendatacommons.org/licenses/dbcl/1-0/) grants use of copyrighted contents subject to ODbL compliance; the [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) governs database rights and conditions. This project keeps raw data local and does not redistribute the CSV. This directory ignores everything except this README, including archives and local receipts.

## Provenance

| Item | Source / status |
| --- | --- |
| Title | IBM HR Analytics Employee Attrition & Performance |
| Kaggle publisher | `pavansubhasht` (not a claim of original authorship) |
| Dataset | https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset |
| File | `WA_Fn-UseC_-HR-Employee-Attrition.csv` |
| Observed file listing | 227,977 bytes; creationDate `2019-09-20 12:14:34.434000` |
| Observed dataset search | lastUpdated `2017-03-31 06:55:16.973000`; these differing timestamps are metadata, not a pinned version |
| License | Kaggle API metadata retrieved during this session reports `DbCL-1.0`; official text requires compliance with ODbL 1.0 |
| Dataset description | Kaggle metadata states this is a fictional dataset created by IBM data scientists; it is not actual employee records |
| Attribution starting point | Dataset title, Kaggle publisher, source URL, access date, `DbCL-1.0`, and ODbL URI; do not claim Kaggle uploader is original author |

## Reproducible procedure

1. The Kaggle API metadata retrieved for this project reported `DbCL-1.0`. Review the linked Kaggle page and both linked license texts before any public redistribution. The contents license requires ODbL compliance. Do not publish the raw CSV or a derivative database unless all applicable notice/share-alike/access obligations are met. A public produced work (for example, dashboard charts) must include an appropriate notice that the data came from this database and is available under ODbL. Record source version and UTC retrieval date in a local `data/raw/source-receipt.md`; the receipt and raw bytes remain local and ignored.
2. Confirm the available CLI and listing without examining credentials:

   ```sh
   kaggle --version
   kaggle datasets files pavansubhasht/ibm-hr-analytics-attrition-dataset
   ```

   Kaggle CLI v1.7.4.5 and the file-listing/metadata commands succeeded in this environment. Do not paste credentials into commands, output, or this repository. If access fails, stop and use Kaggle's documented authentication process privately; the offline validator remains usable.
3. With the source and license identified, print the local-acquisition plan (this only prints commands):

   ```sh
   python -B src/intake.py plan --terms-reviewed
   ```

   This only prints commands; it cannot download. The reviewed command was run from the project root without force/overwrite flags; Kaggle delivered the selected CSV directly (no archive) into `data/raw`. The source contract and local result are recorded below. If a future Kaggle response is an archive, inspect its member names and extract only the expected CSV locally, without overwriting an existing file.
4. Validate and retain the output alongside the receipt:

   ```sh
   python -B src/intake.py validate data/raw/WA_Fn-UseC_-HR-Employee-Attrition.csv
   ```

   Record the emitted SHA-256 and row counts in the receipt. Keep the original bytes locally; do not normalize them before fingerprinting. Reproduction of a previous run requires matching that digest. Upstream version/content changes require explicit review, not an automatic update to the validator.

## Observed acquisition

Kaggle API v1.7.4.5 listed the source CSV and returned metadata reporting `DbCL-1.0` and describing the data as fictional. On 2026-10-16 UTC, the selected CSV was downloaded directly and passed the intake validator: 1,470 rows, 35 columns; Attrition `No`: 1,233, `Yes`: 237. Its exact-byte SHA-256 and source receipt are in ignored `data/raw/source-receipt.md`. Raw CSV, metadata, and receipt remain local and are excluded from Git. Test fixtures are generated examples, not source records. Kaggle metadata and official terms are source evidence, not legal advice.
