"""Compare an educational decision stump with a training-majority baseline."""
import argparse
import csv
import io
import json
from pathlib import Path
import random
import sys

from intake import validate

VERSION = "decision-stump-v1"
FEATURES = ("YearsAtCompany", "TrainingTimesLastYear", "JobSatisfaction", "WorkLifeBalance")
SEED = 42


def counts(rows):
    return {label: sum(row["Attrition"] == label for row in rows) for label in ("No", "Yes")}


def majority(no, yes):
    return "Yes" if yes > no else "No"


def split(rows):
    rng = random.Random(SEED)
    train, test = [], []
    for label in ("No", "Yes"):
        group = [row for row in rows if row["Attrition"] == label]
        if len(group) < 5:
            raise ValueError("need at least 5 rows per class for held-out evaluation")
        rng.shuffle(group)
        cut = len(group) // 5
        test.extend(group[:cut])
        train.extend(group[cut:])
    return train, test


def fit(train):
    """Maximize training balanced accuracy; leaf labels use training majority."""
    totals = counts(train)
    label = majority(totals["No"], totals["Yes"])
    best = {"feature": None, "threshold": None, "left": label, "right": label}
    best_score = 0.5
    for feature in FEATURES:
        ordered = sorted(train, key=lambda row: int(row[feature]))
        left = {"No": 0, "Yes": 0}
        for index, row in enumerate(ordered[:-1]):
            left[row["Attrition"]] += 1
            threshold = int(row[feature])
            if threshold == int(ordered[index + 1][feature]):
                continue
            right = {key: totals[key] - left[key] for key in totals}
            a = majority(left["No"], left["Yes"])
            b = majority(right["No"], right["Yes"])
            correct = {key: (left[key] if a == key else 0) +
                       (right[key] if b == key else 0) for key in totals}
            score = (correct["No"] / totals["No"] + correct["Yes"] / totals["Yes"]) / 2
            if score > best_score:
                best_score = score
                best = {"feature": feature, "threshold": threshold, "left": a, "right": b}
    return best, label


def metrics(test, predict):
    tn = fp = fn = tp = 0
    for row in test:
        positive = predict(row) == "Yes"
        if row["Attrition"] == "Yes":
            tp += positive
            fn += not positive
        else:
            fp += positive
            tn += not positive
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn)
    return {"tn": tn, "fp": fp, "fn": fn, "tp": tp,
            "accuracy": (tn + tp) / len(test), "precision": precision,
            "recall": recall, "f1": 2 * tp / (2 * tp + fp + fn) if tp else 0.0,
            "balanced_accuracy": (recall + tn / (tn + fp)) / 2}


def compare(raw):
    provenance = validate(raw)  # Shared intake contract, before any output writes.
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    train, test = split(rows)
    stump, label = fit(train)

    def predict(row):
        if stump["feature"] is None:
            return stump["left"]
        return stump["left"] if int(row[stump["feature"]]) <= stump["threshold"] else stump["right"]

    return {
        "version": VERSION, "provenance": provenance, "features": list(FEATURES),
        "algorithm": "training balanced-accuracy selection; majority leaves; No on label ties; "
                     "constant then feature order then ascending observed threshold on score ties",
        "split": {"seed": SEED, "method": "stratified shuffled indices; floor(n/5) per class",
                  "train_counts": counts(train), "test_counts": counts(test)},
        "baseline": {"label": label, "test": metrics(test, lambda row: label)},
        "stump": {"fit": stump, "test": metrics(test, predict)},
        "limitations": "Fictional data; educational single holdout, not causal evidence or suitable "
                       "for individual employment decisions. No uncertainty or fairness audit; "
                       "excluded demographics do not eliminate proxy bias. Zero precision/F1 "
                       "denominators are reported as zero. SHA-256 is not authenticity proof.",
        "attribution": "Contains information from IBM HR Analytics Employee Attrition & Performance "
                       "https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset; "
                       "ODbL 1.0 https://opendatacommons.org/licenses/odbl/1-0/; "
                       "contents DbCL 1.0 https://opendatacommons.org/licenses/dbcl/1-0/.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Writes aggregate model.json only. Successful runs overwrite that file; write errors "
        "can leave partial output. Use a dedicated output directory; never source storage."))
    parser.add_argument("csv", help="local CSV validated by the intake contract")
    parser.add_argument("--output", required=True, help="dedicated aggregate output directory")
    args = parser.parse_args(argv)
    try:
        source = Path(args.csv).resolve()
        output = Path(args.output).resolve()
        target = output / "model.json"
        if (source == output or output in source.parents or target.resolve() == source
                or (target.exists() and source.exists() and target.samefile(source))):
            raise ValueError("output must not contain or overwrite the source")
        data = compare(source.read_bytes())
        serialized = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"
        output.mkdir(parents=True, exist_ok=True)
        target.write_text(serialized, encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"model error: {exc}", file=sys.stderr)
        return 1
    train_size = sum(data["split"]["train_counts"].values())
    test_size = sum(data["split"]["test_counts"].values())
    print(f"Model comparison written: {train_size} train; {test_size} test.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
