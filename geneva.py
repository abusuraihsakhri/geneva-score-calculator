#!/usr/bin/env python3
"""
Revised Geneva Score for PE
Revised Geneva (0-22) pulmonary embolism probability with prevalence-calibrated tiers.
Points-based score with tiered action thresholds. Stdlib only.
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

FACTORS = [
        ("Hypotension",1),
        ("Tachycardia",1),
        ("Tachypnea",1),
        ("Fever",1),
        ("Altered mental",1)
]

THRESHOLDS = [(2,"low"),(4,"moderate"),(100,"high")]

def calculate_score(present):
    """present: dict factor->bool or row dict with 1/0."""
    score=0; detail={}
    for name,w in FACTORS:
        # accept 1/0, true/false, yes/no, present key in dict
        val = present.get(name, present.get(name.lower().replace(" ","_"), 0))
        is_pos = str(val).lower() in ("1","true","yes","y") or val==1 or val is True
        # also auto-map common csv columns: age, sex, etc.
        if not is_pos and name=="Age>60":
            try: is_pos = float(present.get("age",0))>60
            except: pass
        if not is_pos and name=="Male":
            is_pos = str(present.get("sex","")).upper()=="M"
        if is_pos:
            score+=w
            detail[name]=w
    # tier
    tier="low"
    for thr,label in THRESHOLDS:
        if score<=thr: tier=label; break
        tier=label
    return {"score": score, "tier": tier, "detail": detail}

def assess_row(row):
    # row is dict from csv
    # map csv columns to present
    present = {}
    for k,v in row.items():
        present[k]=v
        present[k.lower()]=v
    # also map snake
    return calculate_score(present)

def _validate_file_path(path_str: str, must_exist: bool = False) -> Path:
    """Validate and resolve a file path, preventing path traversal."""
    path = Path(path_str).resolve()
    if must_exist and not path.exists():
        raise FileNotFoundError(f"Input file not found: {path_str}")
    if must_exist and not path.is_file():
        raise ValueError(f"Input path is not a file: {path_str}")
    return path


def process_csv(inp, out):
    """Process a CSV file and append Geneva score results.

    Args:
        inp: Path to input CSV file with patient data.
        out: Path to output CSV file for results.

    Returns:
        List of result dictionaries.

    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If input file is empty or has no headers.
    """
    inp_path = _validate_file_path(inp, must_exist=True)
    out_path = _validate_file_path(out, must_exist=False)

    # Ensure output directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(inp_path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        fn = r.fieldnames
        if not fn:
            raise ValueError(f"Input CSV has no headers: {inp}")
        rows = list(r)

    if not rows:
        raise ValueError(f"Input CSV has no data rows: {inp}")

    results = []
    for row in rows:
        res = assess_row(row)
        merged = {
            **row,
            "score": res["score"],
            "tier": res["tier"],
            "detail": ";".join(res["detail"].keys())
        }
        results.append(merged)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fn) + ["score", "tier", "detail"])
        w.writeheader()
        w.writerows(results)

    return results

def build_parser():
    p=argparse.ArgumentParser(prog="geneva", description="Revised Geneva Score for PE")
    sub=p.add_subparsers(dest="cmd", required=True)
    s=sub.add_parser("single"); s.add_argument("--age", type=float); s.add_argument("--sex"); 
    for name,_ in FACTORS:
        s.add_argument("--"+name.lower().replace(" ","_").replace(">","_gt_").replace("/","_"), default="0")
    s.add_argument("--json")
    b=sub.add_parser("batch"); b.add_argument("--input", required=True); b.add_argument("--output", required=True)
    return p

def main(argv=None):
    p = build_parser()
    a = p.parse_args(argv)
    try:
        if a.cmd == "single":
            if a.json:
                try:
                    present = json.loads(a.json)
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
                    return 1
            else:
                present = {k: getattr(a, k) for k in vars(a) if k not in ("cmd", "json")}
            res = calculate_score(present)
            print(res)
            return 0
        if a.cmd == "batch":
            res = process_csv(a.input, a.output)
            print(f"Processed {len(res)} -> {a.output}")
            return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error: I/O error: {e}", file=sys.stderr)
        return 1
    p.print_help()
    return 1

if __name__ == "__main__":
    sys.exit(main())
