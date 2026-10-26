"""Exercise the EDA CLI using isolated fictional inputs."""
import csv
import io
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from test_intake import sample

CLI = Path(__file__).resolve().parents[1] / "src" / "eda.py"


def run(tmp_path, raw=None, *extra):
    source = tmp_path / "input.csv"
    if raw is not None:
        source.write_bytes(raw)
    return subprocess.run(
        [sys.executable, "-B", str(CLI), str(source),
         "--output", str(tmp_path / "reports"), *extra],
        capture_output=True, check=False,
    )


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


def test_cli_writes_only_repeatable_aggregate_artifacts(tmp_path):
    raw = sample()
    result = run(tmp_path, raw)
    assert result.returncode == 0, result.stderr
    assert result.stdout == b"EDA written: 1470 rows; 50.00% attrition.\n"
    assert not result.stderr
    root = tmp_path / "reports"
    first = snapshot(root)
    assert set(first) == {"attrition-eda.md", "data/attrition-counts.csv",
                          "data/overview.csv", "figures/attrition.svg"}
    table = list(csv.DictReader(io.StringIO(
        first["data/attrition-counts.csv"].decode())))
    assert table == [
        {"attrition": "No", "count": "735", "percent": "50.00"},
        {"attrition": "Yes", "count": "735", "percent": "50.00"},
    ]
    overview = list(csv.DictReader(io.StringIO(first["data/overview.csv"].decode())))
    assert overview == [{"rows": "1470", "attrition_percent": "50.00",
                         "majority_label_percent": "50.00"}]
    report = first["attrition-eda.md"].decode()
    for phrase in ("735 of 1,470", "fictional", "causal", "individual",
                   "ODbL", "not held-out", "not authenticity"):
        assert phrase in report
    svg = ET.fromstring(first["figures/attrition.svg"])
    assert svg.attrib["role"] == "img"
    assert "50.00%" in first["figures/attrition.svg"].decode()
    assert b"EmployeeNumber" not in b"".join(first.values())
    assert run(tmp_path, raw).returncode == 0
    assert snapshot(root) == first
    assert (tmp_path / "input.csv").read_bytes() == raw


def test_nonbalanced_distribution_and_majority_baseline(tmp_path):
    raw = sample().replace(b",Yes,", b",No,", 700)
    result = run(tmp_path, raw)
    assert result.returncode == 0, result.stderr
    assert b"2.38% attrition" in result.stdout
    table = (tmp_path / "reports/data/overview.csv").read_text()
    assert "1470,2.38,97.62" in table


@pytest.mark.parametrize("raw", [None, b"bad header\n", sample(count=1469),
                                 sample({"Attrition": "No"}),
                                 sample({"EmployeeNumber": "1"})])
def test_invalid_input_fails_without_writing_report(tmp_path, raw):
    result = run(tmp_path, raw)
    assert result.returncode == 1
    assert not result.stdout
    assert b"eda error:" in result.stderr
    assert b"Traceback" not in result.stderr
    assert not (tmp_path / "reports").exists()


def test_invalid_input_preserves_existing_report(tmp_path):
    assert run(tmp_path, sample()).returncode == 0
    before = snapshot(tmp_path / "reports")
    assert run(tmp_path, b"bad").returncode == 1
    assert snapshot(tmp_path / "reports") == before


def test_output_conflict_is_reported_without_success(tmp_path):
    (tmp_path / "reports").write_text("unrelated")
    result = run(tmp_path, sample())
    assert result.returncode == 1
    assert not result.stdout
    assert b"eda error:" in result.stderr
    assert (tmp_path / "reports").read_text() == "unrelated"


def test_portfolio_artifacts_match_documented_t1_aggregate_counts(tmp_path):
    # Same label totals as T1, but entirely generated employee records.
    result = run(tmp_path, sample().replace(b",Yes,", b",No,", 498))
    assert result.returncode == 0, result.stderr
    # The dashboard is separately owned; EDA must reproduce only these files.
    owned = ("attrition-eda.md", "data/attrition-counts.csv",
             "data/overview.csv", "figures/attrition.svg")
    expected = {name: (CLI.parents[1] / "reports" / name).read_bytes()
                for name in owned}
    assert snapshot(tmp_path / "reports") == expected


def test_missing_arguments_show_usage():
    result = subprocess.run([sys.executable, "-B", str(CLI)], capture_output=True)
    assert result.returncode == 2
    assert not result.stdout
    assert b"usage:" in result.stderr
