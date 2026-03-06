"""Persistent power-duration records store.

Tracks all-time best average powers across standard durations,
enabling PR detection, phenotype classification, and progress comparison.

Follows the fitness_model.py pattern: JSON file in ``data/``, class with
``_load``/``save``/``upsert``, dataclasses for query results.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .models import RecordPoint


STANDARD_DURATIONS = [5, 10, 15, 30, 60, 180, 300, 600, 1200, 1800, 2400, 3600]
DURATION_LABELS = {
    5: "5 sec", 10: "10 sec", 15: "15 sec", 30: "30 sec",
    60: "1 min", 180: "3 min", 300: "5 min", 600: "10 min",
    1200: "20 min", 1800: "30 min", 2400: "40 min", 3600: "60 min",
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PeakRecord:
    """Single all-time best for a duration."""
    duration: int       # seconds
    watts: int
    session_dt: str     # ISO datetime string


@dataclass
class PRCheck:
    """PR check result for a single duration."""
    duration: int
    label: str
    is_pr: bool
    watts: int
    previous_best: int | None
    improvement_watts: int | None   # None when not a PR


@dataclass
class PowerProfile:
    """Phenotype classification based on power curve ratios."""
    phenotype: str      # "TT/Diesel" | "Pursuiter" | "Sprinter" | "All-Rounder" | "Unknown"
    confidence: str     # "High" | "Moderate" | "Low"
    five_min_to_20min: float | None
    five_sec_to_5min: float | None
    one_min_to_20min: float | None
    sessions_count: int


@dataclass
class FTPStalenessCheck:
    """Whether 20-min data suggests FTP needs recalibration."""
    is_stale: bool
    best_20min: int | None
    ftp: int
    sessions_above_threshold: int
    suggested_ftp: int | None   # best_20min * 0.95 if stale


@dataclass
class ProgressComparison:
    """Period-vs-period delta for a single duration."""
    duration: int
    label: str
    current_best: int | None
    reference_best: int | None
    delta_watts: int | None     # current - reference


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------

def extract_peak_powers(records: list[RecordPoint]) -> list[tuple[int, int]]:
    """Sliding-window best average power for standard durations.

    Returns list of (duration_seconds, best_watts) tuples.
    Skips durations longer than the recording.
    """
    powers = [r.power for r in records if r.power is not None]
    if not powers:
        return []

    n_total = len(powers)
    result = []
    for n in STANDARD_DURATIONS:
        if n_total < n:
            continue
        win_sum = float(sum(powers[:n]))
        best = win_sum / n
        for i in range(1, n_total - n + 1):
            win_sum += powers[i + n - 1] - powers[i - 1]
            avg = win_sum / n
            if avg > best:
                best = avg
        result.append((n, round(best)))
    return result


# ---------------------------------------------------------------------------
# Persistent store
# ---------------------------------------------------------------------------

class PowerRecords:
    """Persistent store of per-session peak powers indexed by ISO datetime.

    Storage format (``data/power_records.json``)::

        {
          "records": {
            "5":    {"2026-01-06T10:30:00": 945, "2026-02-15T14:20:00": 958},
            "300":  {"2026-01-06T10:30:00": 328},
            "1200": {"2026-01-06T10:30:00": 294}
          }
        }

    Keys = duration in seconds (string). Values = per-session best watts keyed
    by ISO datetime. Upserts are idempotent — re-running a report is safe.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        # {duration_str: {session_dt_iso: watts}}
        self._records: dict[str, dict[str, int]] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            content = self.path.read_text(encoding="utf-8").strip()
            if content:
                data = json.loads(content)
                self._records = data.get("records", {})

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        sorted_records = {
            str(dur): dict(sorted(self._records.get(str(dur), {}).items()))
            for dur in STANDARD_DURATIONS
            if str(dur) in self._records
        }
        self.path.write_text(
            json.dumps({"records": sorted_records}, indent=2),
            encoding="utf-8",
        )

    def upsert(self, session_dt_iso: str, peaks: list[tuple[int, int]]) -> None:
        """Store per-session peak powers (idempotent)."""
        for duration, watts in peaks:
            key = str(duration)
            if key not in self._records:
                self._records[key] = {}
            self._records[key][session_dt_iso] = watts

    # ------------------------------------------------------------------
    # Query helpers

    def all_time_best(self, duration: int) -> PeakRecord | None:
        """Best ever watts for a duration."""
        entries = self._records.get(str(duration), {})
        if not entries:
            return None
        best_dt = max(entries, key=lambda dt: entries[dt])
        return PeakRecord(duration=duration, watts=entries[best_dt], session_dt=best_dt)

    def best_in_period(self, duration: int, start: str, end: str) -> int | None:
        """Best watts within a date range (ISO string prefix comparison)."""
        entries = self._records.get(str(duration), {})
        vals = [w for dt, w in entries.items() if start <= dt <= end]
        return max(vals) if vals else None

    def check_prs(
        self, session_dt_iso: str, peaks: list[tuple[int, int]]
    ) -> list[PRCheck]:
        """Compare session peaks to all prior records.

        Must be called **before** ``upsert()`` so that the comparison reflects
        the state before this session's data is stored.
        """
        results = []
        for duration, watts in peaks:
            prev = self.all_time_best(duration)
            if prev is None:
                results.append(PRCheck(
                    duration=duration,
                    label=DURATION_LABELS[duration],
                    is_pr=True,
                    watts=watts,
                    previous_best=None,
                    improvement_watts=None,
                ))
            elif watts > prev.watts:
                results.append(PRCheck(
                    duration=duration,
                    label=DURATION_LABELS[duration],
                    is_pr=True,
                    watts=watts,
                    previous_best=prev.watts,
                    improvement_watts=watts - prev.watts,
                ))
            else:
                results.append(PRCheck(
                    duration=duration,
                    label=DURATION_LABELS[duration],
                    is_pr=False,
                    watts=watts,
                    previous_best=prev.watts,
                    improvement_watts=None,
                ))
        return results

    def classify_profile(self) -> PowerProfile | None:
        """Classify power phenotype from all-time best ratios.

        Phenotype rules (primary: 5min:20min ratio):
        - < 1.10x → TT/Diesel
        - > 1.20x → Pursuiter
        - > 3.5x 5s:5min → Sprinter (overrides 5min:20min check)
        - Otherwise → All-Rounder
        """
        best_5s = self.all_time_best(5)
        best_1min = self.all_time_best(60)
        best_5min = self.all_time_best(300)
        best_20min = self.all_time_best(1200)

        sessions_count = len(self._records.get("300", {}))

        five_to_20 = (
            best_5min.watts / best_20min.watts
            if best_5min and best_20min and best_20min.watts > 0
            else None
        )
        five_sec_to_5min = (
            best_5s.watts / best_5min.watts
            if best_5s and best_5min and best_5min.watts > 0
            else None
        )
        one_to_20 = (
            best_1min.watts / best_20min.watts
            if best_1min and best_20min and best_20min.watts > 0
            else None
        )

        if sessions_count >= 30:
            confidence = "High"
        elif sessions_count >= 10:
            confidence = "Moderate"
        else:
            confidence = "Low"

        if five_to_20 is None:
            phenotype = "Unknown"
        elif five_sec_to_5min is not None and five_sec_to_5min > 3.5:
            phenotype = "Sprinter"
        elif five_to_20 < 1.10:
            phenotype = "TT/Diesel"
        elif five_to_20 > 1.20:
            phenotype = "Pursuiter"
        else:
            phenotype = "All-Rounder"

        return PowerProfile(
            phenotype=phenotype,
            confidence=confidence,
            five_min_to_20min=five_to_20,
            five_sec_to_5min=five_sec_to_5min,
            one_min_to_20min=one_to_20,
            sessions_count=sessions_count,
        )

    def check_ftp_staleness(self, ftp: int) -> FTPStalenessCheck:
        """Detect when 20-min data suggests FTP needs recalibration.

        Stale when: best_20min × 0.95 > FTP × 1.05 AND ≥2 sessions with
        20-min best > FTP × 1.05.
        """
        entries = self._records.get("1200", {})
        threshold = ftp * 1.05
        sessions_above = sum(1 for w in entries.values() if w > threshold)
        best_20min_val = max(entries.values()) if entries else None
        is_stale = (
            best_20min_val is not None
            and best_20min_val * 0.95 > threshold
            and sessions_above >= 2
        )
        suggested = round(best_20min_val * 0.95) if is_stale and best_20min_val else None
        return FTPStalenessCheck(
            is_stale=is_stale,
            best_20min=best_20min_val,
            ftp=ftp,
            sessions_above_threshold=sessions_above,
            suggested_ftp=suggested,
        )

    def compare_periods(
        self,
        cur_start: str, cur_end: str,
        ref_start: str, ref_end: str,
    ) -> list[ProgressComparison]:
        """Compare best peaks between two date ranges."""
        result = []
        for dur in STANDARD_DURATIONS:
            cur_best = self.best_in_period(dur, cur_start, cur_end)
            ref_best = self.best_in_period(dur, ref_start, ref_end)
            delta = (
                cur_best - ref_best
                if cur_best is not None and ref_best is not None
                else None
            )
            result.append(ProgressComparison(
                duration=dur,
                label=DURATION_LABELS[dur],
                current_best=cur_best,
                reference_best=ref_best,
                delta_watts=delta,
            ))
        return result
