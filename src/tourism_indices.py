#!/usr/bin/env python3
"""Tea Card Salt Lake daily tourism-weather index calculator.

Builds a local historical reference from the supplied station workbook, then
calculates UVP, clothing demand, human comfort, THI and wind-effect K for one
future daily forecast. No external data source is used.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import openpyxl


STATION_LATITUDE_DEG = 36.7833
MISSING_SENTINEL = 999000.0
SUNSHINE_TOLERANCE_HOURS = 0.05
UVP_REFERENCE_MAX = 14.131644170491846

REQUIRED_HISTORY_COLUMNS = {
    "year": "年", "month": "月", "day": "日", "avg_temp": "平均气温",
    "min_temp": "最低气温", "avg_rh": "平均相对湿度",
    "avg_wind": "平均2分钟风速", "sunshine_hours": "日照时数（直接辐射计算值）",
}


class InputError(ValueError):
    """Raised when an input cannot be used by the agreed rules."""


@dataclass(frozen=True)
class Baseline:
    min_temp_values: tuple[float, ...]
    k_values: tuple[float, ...]
    uvp_thresholds: tuple[float, float, float, float]
    clothing_thresholds: tuple[float, float, float, float]
    reference_start: str
    reference_end: str
    valid_counts: dict[str, int]


def _number(value: Any) -> float | None:
    """Coerce a number; any 999xxx sentinel is missing."""
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) and value < MISSING_SENTINEL else None


def _valid(value: float | None, lower: float, upper: float) -> bool:
    return value is not None and lower <= value <= upper


def _parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError as exc:
        raise InputError("date must use YYYY-MM-DD, for example 2026-07-20") from exc


def solar_geometry(target_date: date, latitude_deg: float = STATION_LATITUDE_DEG) -> tuple[float, float]:
    """Return theoretical day length (hours) and sin(noon solar altitude)."""
    d = target_date.timetuple().tm_yday
    phi = math.radians(latitude_deg)
    declination = math.radians(23.45) * math.sin(2 * math.pi * (284 + d) / 365.0)
    cos_hour_angle = max(-1.0, min(1.0, -math.tan(phi) * math.tan(declination)))
    day_length = 2 * math.degrees(math.acos(cos_hour_angle)) / 15.0
    noon_altitude = math.asin(math.sin(phi) * math.sin(declination) + math.cos(phi) * math.cos(declination))
    return day_length, max(0.0, math.sin(noon_altitude))


def normalise_sunshine(target_date: date, sunshine_hours: float) -> float:
    """Apply the physical day-length quality-control rule."""
    if not _valid(sunshine_hours, 0.0, 24.0):
        raise InputError("sunshine_hours must be between 0 and 24 and cannot be a 999xxx missing code")
    day_length, _ = solar_geometry(target_date)
    if sunshine_hours > day_length + SUNSHINE_TOLERANCE_HOURS:
        raise InputError(
            f"sunshine_hours ({sunshine_hours}) exceeds theoretical day length ({day_length:.2f}) "
            f"by more than {SUNSHINE_TOLERANCE_HOURS:.2f} hours"
        )
    return min(sunshine_hours, day_length)


def calculate_thi(avg_temp: float, avg_rh: float) -> float:
    f = avg_rh / 100.0
    return (1.8 * avg_temp + 32) - 0.55 * (1 - f) * (1.8 * avg_temp - 26)


def calculate_k(avg_temp: float, avg_wind: float, sunshine_hours: float) -> float:
    return -(10 * math.sqrt(avg_wind) + 10.45 - avg_wind) * (33 - avg_temp) + 8.55 * sunshine_hours


def thi_score_and_level(thi: float) -> tuple[int, str]:
    if thi < 40: return -8, "极冷"
    if thi < 45: return -6, "寒冷"
    if thi < 55: return -4, "偏冷"
    if thi < 60: return -2, "偏凉"
    if thi < 65: return 0, "中性"
    if thi < 70: return 2, "偏暖"
    if thi < 75: return 4, "暖热"
    if thi < 80: return 6, "闷热"
    return 8, "极闷热"


def k_score_and_level(k: float) -> tuple[int, str]:
    if k < -1200: return -8, "酷冷"
    if k < -1000: return -6, "冷"
    if k < -800: return -4, "冷凉"
    if k < -600: return -2, "凉"
    if k < -300: return 0, "舒适"
    if k < -200: return 2, "暖"
    if k < -50: return 4, "暖热"
    if k < 80: return 6, "热"
    return 8, "炎热"


def _quantile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("reference distribution is empty")
    position = (len(values) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def _cold_rank(reference: tuple[float, ...], value: float) -> float:
    """Return 0-100; lower temperature/K has a higher cold rank."""
    return 100.0 * (len(reference) - bisect.bisect_left(reference, value)) / len(reference)


def _five_level(value: float, thresholds: tuple[float, float, float, float], labels: tuple[str, ...]) -> str:
    for threshold, label in zip(thresholds, labels):
        if value < threshold:
            return label
    return labels[-1]


def _validate_forecast(forecast: dict[str, Any]) -> tuple[date, float, float, float, float, float]:
    fields = ("date", "avg_temp", "min_temp", "avg_rh", "avg_wind", "sunshine_hours")
    absent = [field for field in fields if field not in forecast]
    if absent:
        raise InputError(f"missing required fields: {', '.join(absent)}")
    target_date = _parse_date(forecast["date"])
    values = {field: _number(forecast[field]) for field in fields if field != "date"}
    if not _valid(values["avg_temp"], -80, 70):
        raise InputError("avg_temp must be between -80 and 70 °C")
    if not _valid(values["min_temp"], -80, 70):
        raise InputError("min_temp must be between -80 and 70 °C")
    if not _valid(values["avg_rh"], 0, 100):
        raise InputError("avg_rh must be between 0 and 100 percent")
    if not _valid(values["avg_wind"], 0, 100):
        raise InputError("avg_wind must be between 0 and 100 m/s")
    sunshine = normalise_sunshine(target_date, values["sunshine_hours"])
    return target_date, values["avg_temp"], values["min_temp"], values["avg_rh"], values["avg_wind"], sunshine


def build_baseline(history_workbook: str | Path) -> Baseline:
    """Build historical reference distributions from a Tea Card station workbook."""
    workbook = openpyxl.load_workbook(history_workbook, read_only=True, data_only=True)
    worksheet = workbook.active
    headers = [cell.value for cell in next(worksheet.iter_rows(min_row=1, max_row=1))]
    positions = {header: idx for idx, header in enumerate(headers)}
    missing = [column for column in REQUIRED_HISTORY_COLUMNS.values() if column not in positions]
    if missing:
        raise InputError(f"history workbook is missing columns: {', '.join(missing)}")

    min_temps: list[float] = []
    k_values: list[float] = []
    uvps: list[float] = []
    paired: list[tuple[float, float]] = []
    dates: list[date] = []
    for row in worksheet.iter_rows(min_row=2, values_only=True):
        try:
            row_date = date(
                int(row[positions[REQUIRED_HISTORY_COLUMNS["year"]]]),
                int(row[positions[REQUIRED_HISTORY_COLUMNS["month"]]]),
                int(row[positions[REQUIRED_HISTORY_COLUMNS["day"]]]),
            )
        except (TypeError, ValueError):
            continue
        dates.append(row_date)
        t = _number(row[positions[REQUIRED_HISTORY_COLUMNS["avg_temp"]]])
        tmin = _number(row[positions[REQUIRED_HISTORY_COLUMNS["min_temp"]]])
        wind = _number(row[positions[REQUIRED_HISTORY_COLUMNS["avg_wind"]]])
        sunshine = _number(row[positions[REQUIRED_HISTORY_COLUMNS["sunshine_hours"]]])
        if _valid(tmin, -80, 70):
            min_temps.append(tmin)
        try:
            sunshine = normalise_sunshine(row_date, sunshine) if sunshine is not None else None
        except InputError:
            sunshine = None
        if sunshine is not None:
            _, noon_sine = solar_geometry(row_date)
            uvps.append(100 * sunshine * noon_sine / UVP_REFERENCE_MAX)
        if _valid(t, -80, 70) and _valid(wind, 0, 100) and sunshine is not None:
            k = calculate_k(t, wind, sunshine)
            k_values.append(k)
            if _valid(tmin, -80, 70):
                paired.append((tmin, k))
    if not dates or not min_temps or not k_values or not uvps or not paired:
        raise InputError("history workbook does not contain enough valid records")

    min_temps.sort()
    k_values.sort()
    min_temp_ref, k_ref = tuple(min_temps), tuple(k_values)
    clothing = sorted(max(_cold_rank(min_temp_ref, tmin), _cold_rank(k_ref, k)) for tmin, k in paired)
    uvps.sort()
    return Baseline(
        min_temp_values=min_temp_ref,
        k_values=k_ref,
        uvp_thresholds=tuple(_quantile(uvps, q) for q in (0.2, 0.4, 0.6, 0.8)),
        clothing_thresholds=tuple(_quantile(clothing, q) for q in (0.2, 0.4, 0.6, 0.8)),
        reference_start=min(dates).isoformat(),
        reference_end=max(dates).isoformat(),
        valid_counts={"min_temp": len(min_temps), "wind_effect_k": len(k_values), "uvp": len(uvps), "clothing": len(clothing)},
    )


def calculate_indices(forecast: dict[str, Any], baseline: Baseline) -> dict[str, Any]:
    """Return the five agreed daily indices for one forecast record."""
    target_date, t, tmin, rh, wind, sunshine = _validate_forecast(forecast)
    thi = calculate_thi(t, rh)
    thi_score, thi_level = thi_score_and_level(thi)
    k = calculate_k(t, wind, sunshine)
    k_score, k_level = k_score_and_level(k)
    _, noon_sine = solar_geometry(target_date)
    uvp = 100 * sunshine * noon_sine / UVP_REFERENCE_MAX
    uvp_level = _five_level(uvp, baseline.uvp_thresholds, ("低暴露潜势", "较低暴露潜势", "中等暴露潜势", "较高暴露潜势", "高暴露潜势"))
    min_temp_rank, k_rank = _cold_rank(baseline.min_temp_values, tmin), _cold_rank(baseline.k_values, k)
    clothing = max(min_temp_rank, k_rank)
    clothing_level = _five_level(clothing, baseline.clothing_thresholds, ("极低保温需求", "较低保温需求", "中等保温需求", "较高保温需求", "高保温需求"))
    deviation = max(abs(thi_score), abs(k_score))
    comfort = 100.0 - 12.5 * deviation
    comfort_level = {100.0: "舒适", 75.0: "舒适", 50.0: "基本舒适", 25.0: "较不舒适", 0.0: "不舒适"}[comfort]
    return {
        "status": "ok",
        "input": {"date": target_date.isoformat(), "avg_temp_c": t, "min_temp_c": tmin, "avg_rh_percent": rh, "avg_wind_mps": wind, "sunshine_hours": round(sunshine, 4)},
        "indices": {
            "uvp": {"name_zh": "茶卡盐湖日照紫外暴露潜势指数", "value": round(uvp, 2), "level": uvp_level, "note": "该指标不是标准UVI。"},
            "clothing": {"name_zh": "茶卡盐湖着装保温需求指数", "value": round(clothing, 2), "level": clothing_level, "min_temp_cold_rank": round(min_temp_rank, 2), "wind_effect_cold_rank": round(k_rank, 2)},
            "comfort": {"name_zh": "人体舒适度", "value": round(comfort, 2), "level": comfort_level, "max_deviation": deviation, "note": "表示未通过着装调整的原始天气舒适度。"},
            "thi": {"name_zh": "温湿度指数", "value": round(thi, 2), "score": thi_score, "level": thi_level},
            "wind_effect_k": {"name_zh": "风效指数", "value": round(k, 2), "score": k_score, "level": k_level},
        },
        "baseline": {
            "reference_period": f"{baseline.reference_start} to {baseline.reference_end}", "valid_counts": baseline.valid_counts,
            "uvp_thresholds": [round(value, 3) for value in baseline.uvp_thresholds],
            "clothing_thresholds": [round(value, 3) for value in baseline.clothing_thresholds],
        },
    }


def _read_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise InputError("input JSON must be a single object")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate five Tea Card Salt Lake daily tourism-weather indices.")
    parser.add_argument("--history", required=True, help="Historical station .xlsx workbook")
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
            forecast = _read_json(args.input_json)
        else:
            forecast = dict(zip(("date", "avg_temp", "min_temp", "avg_rh", "avg_wind", "sunshine_hours"), individual))
        result = calculate_indices(forecast, build_baseline(args.history))
    except (InputError, OSError, openpyxl.utils.exceptions.InvalidFileException) as exc:
        result = {"status": "error", "message": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
