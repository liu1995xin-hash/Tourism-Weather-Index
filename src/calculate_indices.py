#!/usr/bin/env python3
"""Program 2: calculate five indices and their composite from one forecast."""

from __future__ import annotations

import argparse
import json
import sys

import openpyxl

from tourism_indices import InputError, calculate_indices, load_baseline_xlsx, read_forecast_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate five Tea Card tourism-weather indices and their composite from a forecast and frozen baseline."
    )
    parser.add_argument("--baseline", required=True, help="Frozen baseline .xlsx workbook")
    parser.add_argument("--input-json", help="UTF-8 JSON forecast object")
    parser.add_argument("--date", help="Forecast date, YYYY-MM-DD")
    parser.add_argument("--avg-temp", type=float, help="Daily average temperature, °C")
    parser.add_argument("--min-temp", type=float, help="Daily minimum temperature, °C")
    parser.add_argument("--avg-rh", type=float, help="Daily mean relative humidity, percent")
    parser.add_argument("--avg-wind", type=float, help="Daily average 2-minute wind, m/s")
    parser.add_argument("--sunshine-hours", type=float, help="Daily sunshine duration, hours")
    args = parser.parse_args()
    try:
        individual = (args.date, args.avg_temp, args.min_temp, args.avg_rh, args.avg_wind, args.sunshine_hours)
        if args.input_json:
            if any(value is not None for value in individual):
                raise InputError("use either --input-json or all individual forecast arguments, not both")
            forecast = read_forecast_json(args.input_json)
        else:
            forecast = dict(zip(("date", "avg_temp", "min_temp", "avg_rh", "avg_wind", "sunshine_hours"), individual))
        result = calculate_indices(forecast, load_baseline_xlsx(args.baseline))
    except (InputError, OSError, openpyxl.utils.exceptions.InvalidFileException) as exc:
        result = {"status": "error", "message": str(exc)}
    # Keep the command-line result machine-readable across Windows code pages.
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
