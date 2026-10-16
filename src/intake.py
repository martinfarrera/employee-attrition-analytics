"""Offline intake contract and non-executing Kaggle acquisition plan."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

DATASET = "pavansubhasht/ibm-hr-analytics-attrition-dataset"
FILENAME = "WA_Fn-UseC_-HR-Employee-Attrition.csv"
COLUMNS = (
    "Age Attrition BusinessTravel DailyRate Department DistanceFromHome Education "
    "EducationField EmployeeCount EmployeeNumber EnvironmentSatisfaction Gender "
    "HourlyRate JobInvolvement JobLevel JobRole JobSatisfaction MaritalStatus "
    "MonthlyIncome MonthlyRate NumCompaniesWorked Over18 OverTime PercentSalaryHike "
    "PerformanceRating RelationshipSatisfaction StandardHours StockOptionLevel "
    "TotalWorkingYears TrainingTimesLastYear WorkLifeBalance YearsAtCompany "
    "YearsInCurrentRole YearsSinceLastPromotion YearsWithCurrManager"
).split()
CATEGORIES = {
    "Attrition": {"Yes", "No"},
    "BusinessTravel": {"Non-Travel", "Travel_Rarely", "Travel_Frequently"},
    "Department": {"Sales", "Research & Development", "Human Resources"},
    "EducationField": {"Life Sciences", "Other", "Medical", "Marketing", "Technical Degree", "Human Resources"},
    "Gender": {"Female", "Male"},
    "JobRole": {"Sales Executive", "Research Scientist", "Laboratory Technician", "Manufacturing Director", "Healthcare Representative", "Manager", "Sales Representative", "Research Director", "Human Resources"},
    "MaritalStatus": {"Single", "Married", "Divorced"},
    "Over18": {"Y"},
    "OverTime": {"Yes", "No"},
}
RANGES = {
    "Age": (18, 100), "Education": (1, 5), "EmployeeCount": (1, 1),
    "EnvironmentSatisfaction": (1, 4), "JobInvolvement": (1, 4),
    "JobLevel": (1, 5), "JobSatisfaction": (1, 4),
    "PerformanceRating": (1, 4), "RelationshipSatisfaction": (1, 4),
    "StandardHours": (80, 80), "StockOptionLevel": (0, 3),
    "WorkLifeBalance": (1, 4),
}


def validate(raw):
    """Return a stable fingerprint/report; raise ValueError on contract drift."""
    try:
        reader = csv.reader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
        if next(reader, None) != COLUMNS:
            raise ValueError("header must match the ordered 35-column contract")
        ids = set()
        counts = {"No": 0, "Yes": 0}
        rows = 0
        for rows, row in enumerate(reader, 1):
            if len(row) != len(COLUMNS):
                raise ValueError(f"row {rows}: expected 35 fields")
            record = dict(zip(COLUMNS, row))
            for column, value in record.items():
                if not value or value != value.strip():
                    raise ValueError(f"row {rows}: blank or padded {column}")
                if column in CATEGORIES:
                    if value not in CATEGORIES[column]:
                        raise ValueError(f"row {rows}: unknown category in {column}")
                else:
                    if not value.isascii() or not value.isdecimal():
                        raise ValueError(f"row {rows}: expected nonnegative integer in {column}")
                    low, high = RANGES.get(column, (0, float("inf")))
                    if not low <= int(value) <= high:
                        raise ValueError(f"row {rows}: out-of-range {column}")
            employee = int(record["EmployeeNumber"])
            if employee <= 0 or employee in ids:
                raise ValueError(f"row {rows}: duplicate or nonpositive EmployeeNumber")
            ids.add(employee)
            counts[record["Attrition"]] += 1
        if rows != 1470:
            raise ValueError(f"expected 1470 rows; found {rows}")
        if not all(counts.values()):
            raise ValueError("both Attrition labels must be present")
    except (UnicodeError, csv.Error) as exc:
        raise ValueError("invalid UTF-8 CSV") from exc
    return {"dataset": DATASET, "rows": rows, "columns": len(COLUMNS),
            "attrition_counts": counts, "sha256": hashlib.sha256(raw).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="print commands only; never download")
    plan.add_argument("--terms-reviewed", action="store_true")
    check = sub.add_parser("validate", help="validate a local CSV, or '-' for stdin")
    check.add_argument("csv")
    args = parser.parse_args(argv)
    if args.command == "plan":
        if not args.terms_reviewed:
            parser.error("review current Kaggle license/terms first; see data/raw/README.md")
        print(f"kaggle datasets files {DATASET}")
        print(f"kaggle datasets download -d {DATASET} -f {FILENAME} -p data/raw")
        return 0
    try:
        raw = sys.stdin.buffer.read() if args.csv == "-" else Path(args.csv).read_bytes()
        print(json.dumps(validate(raw), sort_keys=True))
    except (OSError, ValueError) as exc:
        print(f"intake error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
