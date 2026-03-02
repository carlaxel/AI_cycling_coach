import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from .models import WorkoutData, HRZoneDistribution

def _load_athlete_config() -> dict:
    try:
        path = Path(__file__).parent.parent / "athlete.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

# Coggan power zones as (lower_bound_pct_ftp, upper_bound_pct_ftp, name)
COGGAN_ZONES = [
    (0.0, 0.55, "Z1 Active Recovery"),
    (0.55, 0.75, "Z2 Endurance"),
    (0.75, 0.90, "Z3 Tempo"),
    (0.90, 1.05, "Z4 Threshold"),
    (1.05, 1.20, "Z5 VO2max"),
    (1.20, 1.50, "Z6 Anaerobic"),
    (1.50, float("inf"), "Z7 Neuromuscular"),
]


@dataclass
class ZoneDistribution:
    zone_name: str
    lower_pct: float
    upper_pct: float
    seconds: int
    percent_of_ride: float


@dataclass
class WorkInterval:
    """A single work interval from a structured workout."""
    lap_number: int
    avg_power: float
    target_low: int
    target_high: int
    deviation_watts: float  # from target midpoint
    deviation_pct: float
    in_target: bool
    elapsed_time: Optional[float] = None
    avg_heart_rate: Optional[int] = None
    efficiency_factor: Optional[float] = None


@dataclass
class IntervalAnalysis:
    """Aggregated interval execution metrics for structured workouts."""
    work_intervals: list[WorkInterval]
    mean_work_power: float
    cv_pct: float  # coefficient of variation
    fade_pct: float  # power change first → last (negative = fade)
    compliance_pct: float  # % of intervals within target
    mean_deviation_watts: float  # mean absolute deviation from target midpoint
    cardiac_drift_pct: Optional[float] = None  # HR change first → last work interval


@dataclass
class AnalysisResult:
    # Raw workout data
    workout: WorkoutData

    # Computed power metrics
    normalized_power: Optional[float] = None
    variability_index: Optional[float] = None
    intensity_factor: Optional[float] = None
    tss: Optional[float] = None

    # Input
    ftp: Optional[int] = None
    weight: Optional[float] = None  # rider weight in kg

    # Zone breakdown (only when FTP provided)
    zones: list[ZoneDistribution] = field(default_factory=list)

    # Interval execution (only for structured workouts with ≥2 work intervals)
    interval_analysis: Optional[IntervalAnalysis] = None


def _analyze_intervals(workout: WorkoutData, ftp: int) -> Optional[IntervalAnalysis]:
    """Analyze structured interval execution quality.

    Identifies work intervals (target power >= 75% FTP) and computes
    fade, consistency, compliance, and cardiac drift metrics.
    Returns None if fewer than 2 work intervals are found.
    """
    threshold = ftp * 0.75
    work_laps = [
        lap for lap in workout.laps
        if lap.target_power_low is not None
        and lap.target_power_low >= threshold
        and lap.avg_power is not None
    ]

    if len(work_laps) < 2:
        return None

    work_intervals = []
    for lap in work_laps:
        t_high = lap.target_power_high if lap.target_power_high is not None else lap.target_power_low
        target_mid = (lap.target_power_low + t_high) / 2
        dev_watts = lap.avg_power - target_mid
        dev_pct = dev_watts / target_mid * 100 if target_mid > 0 else 0.0
        in_target = lap.target_power_low <= lap.avg_power <= t_high

        np_val = lap.normalized_power if lap.normalized_power is not None else lap.avg_power
        ef = round(np_val / lap.avg_heart_rate, 3) if np_val and lap.avg_heart_rate and lap.avg_heart_rate > 0 else None

        work_intervals.append(WorkInterval(
            lap_number=lap.lap_number,
            avg_power=lap.avg_power,
            target_low=lap.target_power_low,
            target_high=t_high,
            deviation_watts=round(dev_watts, 1),
            deviation_pct=round(dev_pct, 1),
            in_target=in_target,
            elapsed_time=lap.elapsed_time,
            avg_heart_rate=lap.avg_heart_rate,
            efficiency_factor=ef,
        ))

    powers = [wi.avg_power for wi in work_intervals]
    mean_power = sum(powers) / len(powers)

    # Coefficient of variation
    variance = sum((p - mean_power) ** 2 for p in powers) / len(powers)
    stdev = variance ** 0.5
    cv = stdev / mean_power * 100 if mean_power > 0 else 0.0

    # Fade: first → last work interval
    fade = (powers[-1] - powers[0]) / powers[0] * 100 if powers[0] > 0 else 0.0

    # Compliance: % of intervals within target range
    in_target_count = sum(1 for wi in work_intervals if wi.in_target)
    compliance = in_target_count / len(work_intervals) * 100

    # Mean absolute deviation from target midpoint
    mean_dev = sum(abs(wi.deviation_watts) for wi in work_intervals) / len(work_intervals)

    # Cardiac drift (conditional on HR data)
    cardiac_drift = None
    hrs = [wi.avg_heart_rate for wi in work_intervals if wi.avg_heart_rate is not None]
    if len(hrs) >= 2 and hrs[0] and hrs[0] > 0:
        cardiac_drift = round((hrs[-1] - hrs[0]) / hrs[0] * 100, 1)

    return IntervalAnalysis(
        work_intervals=work_intervals,
        mean_work_power=round(mean_power, 1),
        cv_pct=round(cv, 1),
        fade_pct=round(fade, 1),
        compliance_pct=round(compliance, 1),
        mean_deviation_watts=round(mean_dev, 1),
        cardiac_drift_pct=cardiac_drift,
    )


def analyze(workout: WorkoutData, ftp: Optional[int] = None, weight: Optional[float] = None) -> AnalysisResult:
    result = AnalysisResult(workout=workout, ftp=ftp, weight=weight)

    athlete_conf = _load_athlete_config()
    lthr = athlete_conf.get("lthr")
    max_hr = athlete_conf.get("max_hr")

    power_values = [r.power for r in workout.records if r.power is not None]
    if not power_values:
        return result

    # Normalized Power: 30-sample rolling mean → ^4 → mean → ^(1/4)
    series = pd.Series(power_values, dtype=float)
    rolling_mean = series.rolling(window=30, min_periods=1).mean()
    np_val = float((rolling_mean**4).mean() ** 0.25)
    result.normalized_power = round(np_val, 1)

    # Variability Index
    avg_power = workout.session.avg_power
    if avg_power is None and power_values:
        avg_power = sum(power_values) / len(power_values)
    if avg_power and avg_power > 0:
        result.variability_index = round(np_val / avg_power, 3)

    if ftp and ftp > 0:
        # Intensity Factor
        if_val = np_val / ftp
        result.intensity_factor = round(if_val, 3)

        # TSS
        duration = workout.session.timer_time or workout.session.elapsed_time
        if duration:
            tss_val = (duration * np_val * if_val) / (ftp * 3600) * 100
            result.tss = round(tss_val, 1)

        # Zone distribution
        total = len(power_values)
        for lower_pct, upper_pct, name in COGGAN_ZONES:
            lo = lower_pct * ftp
            hi = upper_pct * ftp
            count = sum(1 for p in power_values if lo <= p < hi)
            result.zones.append(
                ZoneDistribution(
                    zone_name=name,
                    lower_pct=lower_pct,
                    upper_pct=upper_pct,
                    seconds=count,
                    percent_of_ride=round(count / total * 100, 1) if total else 0.0,
                )
            )

        # Interval execution analysis (structured workouts only)
        result.interval_analysis = _analyze_intervals(workout, ftp)

    # General Efficiency Factor
    if result.normalized_power and workout.session.avg_heart_rate and workout.session.avg_heart_rate > 0:
        workout.session.efficiency_factor = round(result.normalized_power / workout.session.avg_heart_rate, 3)

    # HR Zone Distribution (5-zone model based on LTHR)
    if lthr:
        hr_values = [r.heart_rate for r in workout.records if r.heart_rate is not None]
        if hr_values:
            hr_zones = HRZoneDistribution()
            for hr in hr_values:
                pct = hr / lthr
                if pct < 0.68:
                    hr_zones.z1_time_seconds += 1
                elif pct < 0.84:
                    hr_zones.z2_time_seconds += 1
                elif pct < 0.95:
                    hr_zones.z3_time_seconds += 1
                elif pct < 1.06:
                    hr_zones.z4_time_seconds += 1
                else:
                    hr_zones.z5_time_seconds += 1
            workout.session.hr_zones = hr_zones

    # True Aerobic Decoupling with strict guards
    # Guards: session > 40m, VI <= 1.05, IF between 0.55 and 0.85
    duration = workout.session.timer_time or workout.session.elapsed_time
    if duration and duration >= 40 * 60:
        vi = result.variability_index
        if_val = result.intensity_factor
        if vi and vi <= 1.05 and if_val and 0.55 <= if_val <= 0.85:
            valid_recs = [r for r in workout.records if r.power is not None and r.heart_rate is not None]
            if len(valid_recs) >= 1200:  # at least ~20 mins of valid data to be safe
                half_idx = len(valid_recs) // 2
                
                def calc_half_ef(recs):
                    powers = [r.power for r in recs]
                    hrs = [r.heart_rate for r in recs]
                    if not powers or not hrs: return 0
                    
                    series = pd.Series(powers, dtype=float)
                    np_val = float((series.rolling(window=30, min_periods=1).mean()**4).mean() ** 0.25)
                    avg_hr = sum(hrs) / len(hrs)
                    return np_val / avg_hr if avg_hr > 0 else 0
                
                ef1 = calc_half_ef(valid_recs[:half_idx])
                ef2 = calc_half_ef(valid_recs[half_idx:])
                
                if ef1 > 0 and ef2 > 0:
                    drift = ((ef1 - ef2) / ef1) * 100
                    workout.session.aerobic_decoupling_pct = round(drift, 1)

    return result
