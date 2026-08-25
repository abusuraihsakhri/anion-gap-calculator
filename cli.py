#!/usr/bin/env python3
"""
Command-line interface for the Anion Gap Calculator.

Usage:
  python cli.py calculate --na 140 --cl 100 --hco3 24
  python cli.py calculate --na 140 --cl 100 --hco3 24 --albumin 3.5
  python cli.py calculate --na 140 --cl 100 --hco3 24 --albumin 3.5 --k 4.5
  python cli.py calculate --na 140 --cl 100 --hco3 24 --measured-osm 310 --glucose 100 --bun 15
  python cli.py batch --input input.csv --output results.csv

Python stdlib only.
"""

import argparse
import csv
import json
import sys

import anion_gap


def _print_result(result: dict) -> None:
    """Pretty-print a calculation result to stdout."""
    print("=" * 60)
    print("  ANION GAP CALCULATOR — RESULTS")
    print("=" * 60)

    print(f"  Anion Gap:              {result['anion_gap']:.2f} mEq/L  [{result['ag_status']}]")

    if "anion_gap_k" in result:
        print(f"  Anion Gap (w/ K):       {result['anion_gap_k']:.2f} mEq/L")

    if "corrected_anion_gap" in result:
        print(f"  Corrected AG (albumin): {result['corrected_anion_gap']:.2f} mEq/L  [{result['corrected_ag_status']}]")

    print(f"  Delta Gap:              {result['delta_gap']:.2f} mEq/L")

    if result["delta_ratio"] is not None:
        print(f"  Delta Ratio:            {result['delta_ratio']:.3f}")
    else:
        print(f"  Delta Ratio:            N/A")

    print(f"  Delta Ratio Dx:         {result['delta_ratio_interpretation']}")

    if "osmolal_gap" in result:
        og = result["osmolal_gap"]
        print(f"  ---")
        print(f"  Calculated Osm:         {og['calculated_osm']:.2f} mOsm/kg")
        print(f"  Measured Osm:           {og['measured_osm']:.2f} mOsm/kg")
        print(f"  Osmolal Gap:            {og['osmolal_gap']:.2f} mOsm/kg")
        print(f"  Osmolal Gap Dx:         {og['interpretation']}")

    print(f"  ---")
    print(f"  Summary: {result['summary']}")
    print("=" * 60)


def cmd_calculate(args):
    """Handle the 'calculate' subcommand."""
    result = anion_gap.calculate(
        na=args.na,
        cl=args.cl,
        hco3=args.hco3,
        albumin=args.albumin,
        k=args.k,
        measured_osm=args.measured_osm,
        glucose=args.glucose,
        bun=args.bun,
        ethanol=args.ethanol,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_result(result)
    return 0


def cmd_batch(args):
    """Handle the 'batch' subcommand — process a CSV file."""
    fieldnames_out = None
    results = []

    with open(args.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames_in = list(reader.fieldnames or [])

        for row in reader:
            try:
                na = float(row["na"])
                cl = float(row["cl"])
                hco3 = float(row["hco3"])
            except (KeyError, ValueError) as e:
                print(f"Skipping row (missing/invalid na, cl, or hco3): {e}", file=sys.stderr)
                continue

            albumin = float(row["albumin"]) if row.get("albumin") else None
            k = float(row["k"]) if row.get("k") else None
            measured_osm = float(row["measured_osm"]) if row.get("measured_osm") else None
            glucose = float(row["glucose"]) if row.get("glucose") else None
            bun = float(row["bun"]) if row.get("bun") else None
            ethanol = float(row["ethanol"]) if row.get("ethanol") else None

            result = anion_gap.calculate(
                na=na, cl=cl, hco3=hco3, albumin=albumin, k=k,
                measured_osm=measured_osm, glucose=glucose, bun=bun,
                ethanol=ethanol,
            )

            # Flatten result into CSV columns
            flat = dict(row)
            flat["anion_gap"] = result["anion_gap"]
            flat["ag_status"] = result["ag_status"]
            flat["delta_gap"] = result["delta_gap"]
            flat["delta_ratio"] = result["delta_ratio"] if result["delta_ratio"] is not None else ""
            flat["delta_ratio_interpretation"] = result["delta_ratio_interpretation"]

            if "corrected_anion_gap" in result:
                flat["corrected_anion_gap"] = result["corrected_anion_gap"]
                flat["corrected_ag_status"] = result["corrected_ag_status"]

            if "anion_gap_k" in result:
                flat["anion_gap_k"] = result["anion_gap_k"]

            if "osmolal_gap" in result:
                flat["calculated_osm"] = result["osmolal_gap"]["calculated_osm"]
                flat["measured_osm_out"] = result["osmolal_gap"]["measured_osm"]
                flat["osmolal_gap"] = result["osmolal_gap"]["osmolal_gap"]
                flat["osmolal_gap_interpretation"] = result["osmolal_gap"]["interpretation"]

            flat["summary"] = result["summary"]
            results.append(flat)

    # Determine output fieldnames
    all_keys = set()
    for r in results:
        all_keys.update(r.keys())
    extra = sorted(k for k in all_keys if k not in fieldnames_in)
    fieldnames_out = fieldnames_in + extra

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_out)
        writer.writeheader()
        writer.writerows(results)

    print(f"Processed {len(results)} rows -> {args.output}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="anion-gap-calculator",
        description="Anion Gap Calculator — acid-base interpretation tool",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- calculate ---
    p_calc = sub.add_parser("calculate", help="Single anion gap calculation")
    p_calc.add_argument("--na", type=float, required=True, help="Sodium (mEq/L)")
    p_calc.add_argument("--cl", type=float, required=True, help="Chloride (mEq/L)")
    p_calc.add_argument("--hco3", type=float, required=True, help="Bicarbonate (mEq/L)")
    p_calc.add_argument("--albumin", type=float, default=None, help="Albumin (g/dL)")
    p_calc.add_argument("--k", type=float, default=None, help="Potassium (mEq/L)")
    p_calc.add_argument("--measured-osm", type=float, default=None, help="Measured osmolality (mOsm/kg)")
    p_calc.add_argument("--glucose", type=float, default=None, help="Glucose (mg/dL)")
    p_calc.add_argument("--bun", type=float, default=None, help="BUN (mg/dL)")
    p_calc.add_argument("--ethanol", type=float, default=None, help="Ethanol (mg/dL)")
    p_calc.add_argument("--json", action="store_true", help="Output as JSON")

    # --- batch ---
    p_batch = sub.add_parser("batch", help="Batch process CSV file")
    p_batch.add_argument("--input", "-i", required=True, help="Input CSV path")
    p_batch.add_argument("--output", "-o", default="results.csv", help="Output CSV path")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "calculate":
        return cmd_calculate(args)
    elif args.command == "batch":
        return cmd_batch(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
