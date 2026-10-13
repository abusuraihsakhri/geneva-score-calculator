#!/usr/bin/env python3
"""Revised Geneva Score for pretest probability of pulmonary embolism.

Implements the eight-variable Revised Geneva Score (Le Gal et al., 2006).
This is a pretest probability classification, NOT a PE diagnosis or disposition rule.
"""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

# Canonical, explicit inputs prevent missing clinical findings being treated as absent.
BOOLEAN_FACTORS = {
    "previous_dvt_pe": ("Previous DVT or PE", 3),
    "surgery_or_fracture_1mo": ("Surgery under general anesthesia or lower-limb fracture within 1 month", 2),
    "active_malignancy": ("Active malignancy", 2),
    "unilateral_leg_pain": ("Unilateral lower-limb pain", 3),
    "hemoptysis": ("Hemoptysis", 2),
    "deep_vein_tenderness_and_unilateral_edema": (
        "Pain on deep-vein palpation AND unilateral edema", 4
    ),
}
REQUIRED_FIELDS = ("age", "heart_rate", *BOOLEAN_FACTORS)


def _number(value, name, lower, upper):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number) or not lower <= number <= upper:
        raise ValueError(f"{name} must be between {lower} and {upper}")
    return number


def _boolean(value, name):
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("1", "true", "yes", "y"):
            return True
        if normalized in ("0", "false", "no", "n"):
            return False
    raise ValueError(f"{name} must be true/false or 1/0 (not blank)")


def calculate_score(present):
    """Calculate a Revised Geneva score from all eight required criteria.

    age: years; heart_rate: beats/minute; other fields: boolean.
    Missing or invalid criteria raise ValueError rather than score as negative.
    Returns score (0-22), tier, and positive components.
    """
    if not isinstance(present, dict):
        raise ValueError("Input must be an object with all clinical criteria")
    missing = [field for field in REQUIRED_FIELDS if field not in present]
    if missing:
        raise ValueError("Missing required criteria: " + ", ".join(missing))

    age = _number(present["age"], "age", 0, 120)
    heart_rate = _number(present["heart_rate"], "heart_rate", 1, 300)
    detail = {}
    if age > 65:
        detail["Age >65 years"] = 1
    if heart_rate >= 95:
        detail["Heart rate >=95 bpm"] = 5
    elif heart_rate >= 75:
        detail["Heart rate 75-94 bpm"] = 3

    for field, (label, points) in BOOLEAN_FACTORS.items():
        if _boolean(present[field], field):
            detail[label] = points

    score = sum(detail.values())
    tier = "low" if score <= 3 else "intermediate" if score <= 10 else "high"
    return {"score": score, "tier": tier, "detail": detail}


def assess_row(row):
    """Score one CSV record using the canonical field names."""
    return calculate_score(row)


def _validate_file_path(path_str, must_exist=False):
    """Resolve an input/output path. This does not implement a filesystem sandbox."""
    path = Path(path_str).expanduser().resolve()
    if must_exist and not path.is_file():
        raise FileNotFoundError(f"Input CSV file not found: {path_str}")
    return path


def _safe_spreadsheet_cell(value):
    """Neutralize spreadsheet formula injection in forwarded CSV text fields."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def process_csv(inp, out):
    """Validate and process a CSV containing every required criterion."""
    inp_path = _validate_file_path(inp, must_exist=True)
    out_path = _validate_file_path(out)
    if inp_path == out_path:
        raise ValueError("Input and output CSV must be different files")

    with inp_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        if not fields:
            raise ValueError("Input CSV has no headers")
        if len(fields) != len(set(fields)):
            raise ValueError("Duplicate CSV column names are not allowed")
        missing = [key for key in REQUIRED_FIELDS if key not in fields]
        if missing:
            raise ValueError("Missing required CSV columns: " + ", ".join(missing))
        if any(key in fields for key in ("score", "tier", "detail")):
            raise ValueError("CSV contains a reserved output column")
        rows = list(reader)

    if not rows:
        raise ValueError("Input CSV has no data rows")

    results = []
    for line_number, row in enumerate(rows, start=2):
        if None in row:
            raise ValueError(f"Too many columns on CSV row {line_number}")
        try:
            result = assess_row(row)
        except ValueError as exc:
            raise ValueError(f"CSV row {line_number}: {exc}") from exc
        results.append({**row, "score": result["score"], "tier": result["tier"],
                        "detail": ";".join(result["detail"])})

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[*fields, "score", "tier", "detail"])
        writer.writeheader()
        for result in results:
            writer.writerow({k: _safe_spreadsheet_cell(v) for k, v in result.items()})
    return results


def build_parser():
    parser = argparse.ArgumentParser(description="Revised Geneva PE pretest probability score")
    commands = parser.add_subparsers(dest="cmd", required=True)
    single = commands.add_parser("single", help="Score all eight criteria")
    single.add_argument("--json", help="JSON object with all eight criteria")
    single.add_argument("--age", type=float)
    single.add_argument("--heart-rate", type=float)
    for name in BOOLEAN_FACTORS:
        switch = name.replace("_", "-")
        group = single.add_mutually_exclusive_group()
        group.add_argument("--" + switch, dest=name, action="store_true")
        group.add_argument("--no-" + switch, dest=name, action="store_false")
    # Omission is unknown, never implicitly a negative clinical finding.
    single.set_defaults(**{name: None for name in BOOLEAN_FACTORS})
    batch = commands.add_parser("batch", help="Score a CSV of clinical criteria")
    batch.add_argument("--input", required=True)
    batch.add_argument("--output", required=True)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "single":
            if args.json is not None:
                try:
                    present = json.loads(args.json)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON: {exc}") from exc
            else:
                present = {key: getattr(args, key) for key in BOOLEAN_FACTORS}
                present.update(age=args.age, heart_rate=args.heart_rate)
            print(json.dumps(calculate_score(present), sort_keys=True))
            return 0
        results = process_csv(args.input, args.output)
        print(f"Processed {len(results)} rows -> {args.output}")
        return 0
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
