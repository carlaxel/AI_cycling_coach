#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Power PR report — extracts best power for each duration over:
  - Last 30 days
  - Last 90 days
  - Last 365 days (year)
  - All time
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "power_records.json"
ATHLETE_FILE = Path(__file__).parent / "athlete.json"

DURATION_LABELS = {
    "5": "5s",
    "10": "10s",
    "15": "15s",
    "30": "30s",
    "60": "1min",
    "180": "3min",
    "300": "5min",
    "600": "10min",
    "1200": "20min",
    "1800": "30min",
    "2400": "40min",
    "3600": "60min",
}

WINDOWS = {
    "30d": 30,
    "90d": 90,
    "1yr": 365,
    "all": None,
}


def load_data():
    with open(DATA_FILE) as f:
        records = json.load(f)["records"]
    with open(ATHLETE_FILE) as f:
        athlete = json.load(f)
    return records, athlete


def best_in_window(entries: dict[str, int], cutoff: datetime | None) -> tuple[int, str] | None:
    """Return (best_watts, date_str) for entries after cutoff, or None if no data."""
    best_watts = 0
    best_date = ""
    for ts, watts in entries.items():
        dt = datetime.fromisoformat(ts)
        if cutoff and dt < cutoff:
            continue
        if watts > best_watts:
            best_watts = watts
            best_date = dt.strftime("%Y-%m-%d")
    return (best_watts, best_date) if best_watts else None


def format_row(label: str, result: tuple[int, str] | None, weight_kg: float) -> str:
    if result is None:
        return f"  {label:<8} {'—':>6}  {'—':>7}  {'—':>12}"
    watts, date = result
    wpkg = watts / weight_kg
    return f"  {label:<8} {watts:>5}W  {wpkg:>5.2f} W/kg  {date:>12}"


def main():
    records, athlete = load_data()
    weight = athlete["weight_kg"]
    now = datetime.now(tz=timezone.utc)

    cutoffs = {
        "30d": now - timedelta(days=30),
        "90d": now - timedelta(days=90),
        "1yr": now - timedelta(days=365),
        "all": None,
    }

    print(f"\n{'─' * 52}")
    print(f"  Power PRs  (weight: {weight} kg, FTP: {athlete['ftp']}W)")
    print(f"{'─' * 52}")

    header = f"  {'Dur':<8} {'30d':>11}  {'90d':>11}  {'1yr':>11}  {'All time':>11}"
    print(header)
    print(f"  {'─'*8}  {'─'*11}  {'─'*11}  {'─'*11}  {'─'*11}")

    for dur_key, dur_label in DURATION_LABELS.items():
        if dur_key not in records:
            continue
        entries = records[dur_key]
        row_parts = [f"  {dur_label:<8}"]
        for window_key in ("30d", "90d", "1yr", "all"):
            result = best_in_window(entries, cutoffs[window_key])
            if result is None:
                row_parts.append(f"{'—':>5}       ")
            else:
                watts, date = result
                wpkg = watts / weight
                row_parts.append(f"{watts:>5}W {wpkg:.2f}")
        print("  ".join(row_parts))

    # Detailed view per window
    for window_key, window_label in [("30d", "Last 30 days"), ("90d", "Last 90 days"),
                                      ("1yr", "Last year"), ("all", "All time")]:
        print(f"\n{'─' * 52}")
        print(f"  {window_label}")
        print(f"{'─' * 52}")
        print(f"  {'Duration':<8} {'Watts':>6}  {'W/kg':>7}  {'Date':>12}")
        print(f"  {'─'*8}  {'─'*5}  {'─'*7}  {'─'*10}")
        for dur_key, dur_label in DURATION_LABELS.items():
            if dur_key not in records:
                continue
            result = best_in_window(records[dur_key], cutoffs[window_key])
            print(format_row(dur_label, result, weight))

    print(f"\n{'─' * 52}\n")


if __name__ == "__main__":
    main()
