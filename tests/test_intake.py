"""Public CLI checks use generated rows, never the source dataset."""
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

import pytest

CLI = Path(__file__).resolve().parents[1] / "src" / "intake.py"
HEADER = "Age,Attrition,BusinessTravel,DailyRate,Department,DistanceFromHome,Education,EducationField,EmployeeCount,EmployeeNumber,EnvironmentSatisfaction,Gender,HourlyRate,JobInvolvement,JobLevel,JobRole,JobSatisfaction,MaritalStatus,MonthlyIncome,MonthlyRate,NumCompaniesWorked,Over18,OverTime,PercentSalaryHike,PerformanceRating,RelationshipSatisfaction,StandardHours,StockOptionLevel,TotalWorkingYears,TrainingTimesLastYear,WorkLifeBalance,YearsAtCompany,YearsInCurrentRole,YearsSinceLastPromotion,YearsWithCurrManager".split(",")
BASE = "30,No,Non-Travel,100,Sales,1,1,Other,1,1,1,Female,10,1,1,Manager,1,Single,1000,1000,0,Y,No,10,3,1,80,0,5,1,1,2,1,0,1".split(",")


def sample(change=None, count=1470, header=None):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(HEADER if header is None else header)
    for index in range(count):
        row = dict(zip(HEADER, BASE))
        row["EmployeeNumber"] = str(index + 1)
        row["Attrition"] = "Yes" if index % 2 else "No"
        if change:
            row.update(change)
        writer.writerow(row.values())
    return output.getvalue().encode()


def run(*args, raw=None):
    return subprocess.run([sys.executable, "-B", str(CLI), *args], input=raw,
                          capture_output=True, check=False)


def test_valid_input_has_repeatable_report_and_exact_fingerprint():
    raw = sample()
    first = run("validate", "-", raw=raw)
    assert first.returncode == 0, first.stderr
    assert first.stdout == run("validate", "-", raw=raw).stdout
    assert json.loads(first.stdout) == {
        "dataset": "pavansubhasht/ibm-hr-analytics-attrition-dataset",
        "rows": 1470, "columns": 35, "attrition_counts": {"Yes": 735, "No": 735},
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


@pytest.mark.parametrize("change,message", [
    ({"Age": ""}, b"blank"), ({"Age": "NaN"}, b"integer"),
    ({"Age": "-1"}, b"integer"), ({"Age": "17"}, b"out-of-range"),
    ({"Attrition": "Maybe"}, b"unknown category"),
    ({"Attrition": "No"}, b"both Attrition"),
    ({"EmployeeNumber": "1"}, b"duplicate"),
    ({"EmployeeNumber": "0"}, b"nonpositive"),
    ({"StandardHours": "40"}, b"out-of-range"),
    ({"Department": " Sales"}, b"padded"),
])
def test_rejects_invalid_values(change, message):
    result = run("validate", "-", raw=sample(change))
    assert result.returncode == 1
    assert message in result.stderr
    assert not result.stdout


@pytest.mark.parametrize("raw,message", [
    (sample(count=0), b"1470"), (sample(count=1469), b"1470"),
    (sample(count=1471), b"1470"),
    (sample(header=HEADER[::-1]), b"header"),
    (sample(header=HEADER[:-1] + [HEADER[0]]), b"header"),
    (b"\xff", b"UTF-8"),
    ((",".join(HEADER) + "\n1,2\n").encode(), b"35 fields"),
])
def test_rejects_shape_and_encoding_drift(raw, message):
    result = run("validate", "-", raw=raw)
    assert result.returncode == 1
    assert message in result.stderr


def test_missing_local_file_fails_cleanly():
    result = run("validate", str(CLI.parent / "does-not-exist.csv"))
    assert result.returncode == 1
    assert b"intake error" in result.stderr
    assert b"Traceback" not in result.stderr


def test_download_plan_is_gated_and_only_prints_commands():
    rejected = run("plan")
    assert rejected.returncode == 2
    assert b"review current Kaggle license" in rejected.stderr
    accepted = run("plan", "--terms-reviewed")
    assert accepted.returncode == 0
    assert accepted.stdout.decode().splitlines() == [
        "kaggle datasets files pavansubhasht/ibm-hr-analytics-attrition-dataset",
        "kaggle datasets download -d pavansubhasht/ibm-hr-analytics-attrition-dataset -f WA_Fn-UseC_-HR-Employee-Attrition.csv -p data/raw",
    ]
