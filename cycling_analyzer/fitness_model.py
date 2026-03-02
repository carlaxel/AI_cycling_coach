"""Fitness-fatigue (Performance Management Chart) model.

Computes CTL, ATL, TSB from a persistent session TSS history stored in
``data/fitness_history.json``.

CTL — Chronic Training Load (42-day EMA of daily TSS) — represents fitness.
ATL — Acute Training Load (7-day EMA of daily TSS) — represents fatigue.
TSB — Training Stress Balance (CTL − ATL) — represents form/freshness.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

CTL_TC = 42  # Chronic Training Load time constant (days)
ATL_TC = 7   # Acute Training Load time constant (days)


@dataclass
class FitnessSnapshot:
    """CTL/ATL/TSB state at a specific date."""

    date: date
    ctl: float  # Chronic Training Load (fitness)
    atl: float  # Acute Training Load (fatigue)
    tsb: float  # Training Stress Balance (form = CTL − ATL)

    @property
    def form_label(self) -> str:
        if self.tsb > 10:
            return "Fresh"
        elif self.tsb > 0:
            return "Neutral+"
        elif self.tsb > -10:
            return "Neutral−"
        elif self.tsb > -20:
            return "Fatigued"
        elif self.tsb > -30:
            return "Very Fatigued"
        return "Overreached"


@dataclass
class FitnessMetrics:
    """Fitness model results for a weekly report."""

    current: FitnessSnapshot
    one_week_ago: FitnessSnapshot
    four_weeks_ago: FitnessSnapshot
    history_days: int  # days of data seeding the model

    @property
    def ctl_weekly_ramp(self) -> float:
        """CTL gained over the past 7 days."""
        return self.current.ctl - self.one_week_ago.ctl

    @property
    def ramp_label(self) -> str:
        rate = self.ctl_weekly_ramp
        if rate > 7:
            return "⚠ Excessive (>7 pts/week)"
        elif rate > 3:
            return "Elevated (3–7 pts/week)"
        elif rate >= 0:
            return "OK"
        return "Decreasing"


class FitnessHistory:
    """Persistent store of per-session TSS, indexed by session ISO datetime string.

    Storage format (``data/fitness_history.json``)::

        {
          "sessions": {
            "2026-01-06T10:30:00": 68.5,
            "2026-01-08T09:15:00": 82.0
          }
        }

    Using session datetimes as keys prevents double-counting if a report is
    re-generated, while still supporting multiple sessions on the same day.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._sessions: dict[str, float] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._sessions = data.get("sessions", {})

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"sessions": dict(sorted(self._sessions.items()))}, indent=2),
            encoding="utf-8",
        )

    def upsert(self, session_dt_iso: str, tss: float) -> None:
        """Record (or overwrite) TSS for a session identified by its ISO datetime."""
        self._sessions[session_dt_iso] = tss

    # ------------------------------------------------------------------
    # Internal helpers

    def _daily_totals(self) -> dict[date, float]:
        """Aggregate per-session TSS values into daily totals."""
        totals: dict[date, float] = {}
        for dt_str, tss in self._sessions.items():
            d = date.fromisoformat(dt_str[:10])
            totals[d] = totals.get(d, 0.0) + tss
        return totals

    # ------------------------------------------------------------------
    # Computation

    def snapshot(self, as_of: date) -> FitnessSnapshot:
        """Compute CTL/ATL/TSB as of ``as_of`` using all stored history.

        Seeds the EMA from the earliest date in the history (or 42 days back if
        empty), starting at CTL=ATL=0.  Values are underestimated until ~42 days
        of history have accumulated.
        """
        daily = self._daily_totals()
        start = min(daily.keys()) if daily else as_of - timedelta(days=CTL_TC)

        ctl = 0.0
        atl = 0.0
        current = start
        while current <= as_of:
            tss = daily.get(current, 0.0)
            ctl += (tss - ctl) / CTL_TC
            atl += (tss - atl) / ATL_TC
            current += timedelta(days=1)

        return FitnessSnapshot(date=as_of, ctl=ctl, atl=atl, tsb=ctl - atl)

    def compute_metrics(self, as_of: date) -> FitnessMetrics:
        """Return fitness metrics with current, 1-week, and 4-week snapshots."""
        daily = self._daily_totals()
        history_days = (as_of - min(daily.keys())).days + 1 if daily else 0
        return FitnessMetrics(
            current=self.snapshot(as_of),
            one_week_ago=self.snapshot(as_of - timedelta(weeks=1)),
            four_weeks_ago=self.snapshot(as_of - timedelta(weeks=4)),
            history_days=history_days,
        )
