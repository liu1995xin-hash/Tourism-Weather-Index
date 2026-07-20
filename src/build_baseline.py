#!/usr/bin/env python3
"""Program 1: construct a frozen Tea Card tourism-weather baseline workbook."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import openpyxl

from tourism_indices import InputError, build_baseline, write_baseline_xlsx


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a frozen Tea Card tourism-weather baseline .xlsx from historical station data."
    )
    parser.add_argument("--history", required=True, help="Historical station .xlsx workbook")
    parser.add_argument("--output", required=True, help="Output frozen baseline .xlsx workbook")
    args = parser.parse_args()
    try:
        baseline = build_baseline(args.history)
        write_baseline_xlsx(baseline, args.output)
        result = {
            "status": "ok",
            "baseline_workbook": str(Path(args.output)),
            "method_version": "1.1-altitude-uvp",
            "reference_period": f"{baseline.reference_start} to {baseline.reference_end}",
            "valid_counts": baseline.valid_counts,
            "uvp_thresholds": [round(value, 3) for value in baseline.uvp_thresholds],
            "clothing_thresholds": [round(value, 3) for value in baseline.clothing_thresholds],
            "source_workbook_sha256": baseline.source_workbook_sha256,
        }
    except (InputError, OSError, openpyxl.utils.exceptions.InvalidFileException) as exc:
        result = {"status": "error", "message": str(exc)}
    # Keep the command-line result machine-readable across Windows code pages.
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
