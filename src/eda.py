"""Deterministic aggregate-only EDA; no third-party runtime dependencies."""
import argparse
import csv
import io
from pathlib import Path
import sys

from intake import validate


def csv_table(header, rows):
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return output.getvalue()


def artifacts(summary):
    """Render from intake aggregates only, never from employee records."""
    total = summary["rows"]
    counts = summary["attrition_counts"]
    rate = counts["Yes"] / total * 100
    majority = max(counts.values()) / total * 100
    table = csv_table(["attrition", "count", "percent"],
                      [(label, counts[label], f"{counts[label] / total * 100:.2f}")
                       for label in ("No", "Yes")])
    overview = csv_table(["rows", "attrition_percent", "majority_label_percent"],
                         [(total, f"{rate:.2f}", f"{majority:.2f}")])
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 220"',
        '     role="img" aria-labelledby="title description">',
        '  <title id="title">Overall attrition distribution</title>',
        '  <desc id="description">Percentage of validated rows by Attrition label;',
        '  bars use a common zero to 100 percent scale. Counts appear in labels.</desc>',
        '  <rect width="640" height="220" fill="white"/>',
        '  <g font-family="sans-serif" font-size="16" fill="#172b4d">',
        '    <text x="20" y="28">Attrition — share of validated rows</text>',
    ]
    for label, y in (("No", 60), ("Yes", 120)):
        percent = counts[label] / total * 100
        svg.extend([
            f'    <text x="20" y="{y + 20}">{label}</text>',
            f'    <rect x="70" y="{y}" width="300" height="28" fill="#edf0f5"/>',
            f'    <rect x="70" y="{y}" width="{percent * 3:.2f}" height="28" fill="#245b91"/>',
            f'    <text x="385" y="{y + 20}">{percent:.2f}% (n={counts[label]:,})</text>',
        ])
    svg.extend(['    <text x="70" y="190">0%</text>',
                '    <text x="325" y="190">100%</text>', '  </g>', '</svg>'])
    report = f"""# Attrition EDA — overall distribution

**{counts['Yes']:,} of {total:,} validated rows ({rate:.2f}%) have Attrition = Yes.**
The remaining {counts['No']:,} ({100 - rate:.2f}%) have Attrition = No.
This first descriptive slice summarizes labels, not reasons for leaving.

![Overall attrition distribution](figures/attrition.svg)

## Evidence and method

- [Label counts and percentages](data/attrition-counts.csv) use all validated rows as denominator.
- [Overview](data/overview.csv) includes the majority-label share: {majority:.2f}%.
  Always predicting the more common label would obtain this in-sample accuracy;
  this is not held-out evaluation or a trained model. Accuracy alone can hide
  poor detection of the minority class; T3 must compare held-out class-sensitive metrics.
- Input must pass the unchanged intake contract (1,470 rows, 35 ordered columns,
  valid values, unique identifiers, both labels). No cleaning or row exclusion occurs.
- Percentages are rounded to two decimals; tables and figure have fixed label order.
  Outputs contain only global aggregates, no employee-level records or identifiers.
- Structural validation establishes compatibility, not authenticity. Reproduce from
  the same locally validated source bytes; acquisition may change upstream.

## Limitations and next slice

The source is described as fictional IBM data. These are descriptive sample
frequencies, not population estimates, causal effects, or an annual attrition rate:
no observation window or sampling design is established here. Global counts do
not establish subgroup differences or explain attrition. No uncertainty intervals
are offered without a justified sampling model. Do not use this work for individual
employment decisions. Subgroup exploration, modeling, and a demo remain future work.

## Source and attribution

Contains information from [IBM HR Analytics Employee Attrition & Performance](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset),
made available under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/);
contents are licensed under [DbCL 1.0](https://opendatacommons.org/licenses/dbcl/1-0/).
No raw data is redistributed. See [project instructions](../README.md) for acquisition
and regeneration. Validation does not establish redistribution clearance.
"""
    return {"attrition-eda.md": report, "data/attrition-counts.csv": table,
            "data/overview.csv": overview, "figures/attrition.svg": "\n".join(svg) + "\n"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", help="local intake-compatible CSV")
    parser.add_argument("--output", type=Path, default=Path("reports"))
    args = parser.parse_args(argv)
    try:
        summary = validate(Path(args.csv).read_bytes())
        rendered = artifacts(summary)
        # Validate and render everything before creating any output files.
        for relative, content in rendered.items():
            target = args.output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"eda error: {exc}", file=sys.stderr)
        return 1
    rate = summary["attrition_counts"]["Yes"] / summary["rows"] * 100
    print(f"EDA written: {summary['rows']} rows; {rate:.2f}% attrition.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
