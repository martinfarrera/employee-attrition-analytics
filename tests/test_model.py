"""Public modeling contract, using generated rows only."""
import csv
import hashlib
import io
import json
from pathlib import Path
import random
import subprocess
import sys

import pytest

from test_intake import sample

CLI = Path(__file__).resolve().parents[1] / "src/model.py"


def dataset(positives=735, signal=False, alter_holdout=False):
    rows = list(csv.DictReader(io.StringIO(sample().decode())))
    for i, row in enumerate(rows):
        row["Attrition"] = "Yes" if i < positives else "No"
        row["YearsAtCompany"] = "9" if signal and i < positives else "1"
    if alter_holdout:
        rng = random.Random(42)
        for label in ("No", "Yes"):
            indices = [i for i, row in enumerate(rows) if row["Attrition"] == label]
            rng.shuffle(indices)
            for i in indices[:len(indices) // 5]:
                rows[i]["YearsAtCompany"] = "999"  # unseen held-out value
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def run(tmp_path, raw, output=None):
    source = tmp_path / "input.csv"
    source.write_bytes(raw)
    result = subprocess.run(
        [sys.executable, "-B", str(CLI), str(source), "--output",
         str(output or tmp_path / "output")], capture_output=True,
    )
    assert source.read_bytes() == raw
    return result


def report(tmp_path):
    return json.loads((tmp_path / "output/model.json").read_text())


def test_reproducible_held_out_separable_classifier(tmp_path):
    raw = dataset(signal=True)
    result = run(tmp_path, raw)
    assert (result.returncode, result.stdout, result.stderr) == (
        0, b"Model comparison written: 1176 train; 294 test.\n", b"")
    first = (tmp_path / "output/model.json").read_bytes()
    assert run(tmp_path, raw).returncode == 0
    assert (tmp_path / "output/model.json").read_bytes() == first
    assert [p.name for p in (tmp_path / "output").iterdir()] == ["model.json"]
    data = report(tmp_path)
    assert data["provenance"]["sha256"] == hashlib.sha256(raw).hexdigest()
    assert data["split"] == {"seed": 42, "method": "stratified shuffled indices; floor(n/5) per class",
                             "train_counts": {"No": 588, "Yes": 588},
                             "test_counts": {"No": 147, "Yes": 147}}
    assert data["stump"]["fit"] == {"feature": "YearsAtCompany", "threshold": 1,
                                     "left": "No", "right": "Yes"}
    assert data["stump"]["test"] == {"tn": 147, "fp": 0, "fn": 0, "tp": 147,
        "accuracy": 1.0, "precision": 1.0, "recall": 1.0, "f1": 1.0, "balanced_accuracy": 1.0}
    assert data["baseline"]["label"] == "No"  # training tie
    assert b"EmployeeNumber" not in first
    assert "individual employment decisions" in data["limitations"]


def test_imbalanced_baseline_and_constant_feature_fallback(tmp_path):
    result = run(tmp_path, dataset(positives=35))
    assert (result.returncode, result.stdout, result.stderr) == (
        0, b"Model comparison written: 1176 train; 294 test.\n", b"")
    data = report(tmp_path)
    expected = {"tn": 287, "fp": 0, "fn": 7, "tp": 0,
                "accuracy": 287 / 294, "precision": 0.0, "recall": 0.0,
                "f1": 0.0, "balanced_accuracy": 0.5}
    assert data["baseline"]["test"] == expected == data["stump"]["test"]
    assert data["stump"]["fit"]["feature"] is None
    assert data["provenance"]["attrition_counts"] == {"No": 1435, "Yes": 35}


def test_holdout_features_cannot_change_training_selection(tmp_path):
    assert run(tmp_path, dataset(signal=True)).returncode == 0
    before = report(tmp_path)
    assert run(tmp_path, dataset(signal=True, alter_holdout=True)).returncode == 0
    after = report(tmp_path)
    assert before["stump"]["fit"] == after["stump"]["fit"]
    assert before["baseline"]["label"] == after["baseline"]["label"]
    assert before["stump"]["test"] != after["stump"]["test"]


@pytest.mark.parametrize("raw,message", [
    (b"bad\n", "header must match the ordered 35-column contract"),
    (sample(count=1469), "expected 1470 rows; found 1469"),
    (dataset(positives=1), "need at least 5 rows per class for held-out evaluation"),
])
def test_rejection_never_creates_or_changes_output(tmp_path, raw, message):
    for existing in (False, True):
        if existing:
            (tmp_path / "output").mkdir()
            (tmp_path / "output/model.json").write_bytes(b"prior report")
        result = run(tmp_path, raw)
        assert (result.returncode, result.stdout, result.stderr) == (
            1, b"", f"model error: {message}\n".encode())
        if existing:
            assert (tmp_path / "output/model.json").read_bytes() == b"prior report"
        else:
            assert not (tmp_path / "output").exists()


def test_source_collision_and_output_conflict(tmp_path):
    raw = dataset()
    for output in (tmp_path, tmp_path / "input.csv"):
        result = run(tmp_path, raw, output)
        assert (result.returncode, result.stdout, result.stderr) == (
            1, b"", b"model error: output must not contain or overwrite the source\n")
    (tmp_path / "output").write_bytes(b"unrelated")
    result = run(tmp_path, raw)
    assert result.returncode == 1 and not result.stdout
    assert result.stderr.startswith(b"model error:") and b"Traceback" not in result.stderr
    assert (tmp_path / "output").read_bytes() == b"unrelated"


def test_help_and_usage():
    help_result = subprocess.run([sys.executable, "-B", str(CLI), "--help"], capture_output=True)
    assert help_result.returncode == 0 and not help_result.stderr
    for text in (b"--output", b"overwrite", b"partial", b"educational"):
        assert text in help_result.stdout
    usage = subprocess.run([sys.executable, "-B", str(CLI)], capture_output=True)
    assert usage.returncode == 2 and not usage.stdout
    assert usage.stderr.startswith(b"usage:")
