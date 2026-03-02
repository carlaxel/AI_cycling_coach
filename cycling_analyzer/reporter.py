"""Report generation for cycling training analysis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .analyzer import AnalysisResult, IntervalAnalysis, ZoneDistribution, COGGAN_ZONES
from .fitness_model import CTL_TC, FitnessMetrics, FitnessSnapshot
from .models import RecordPoint
from .utils import fmt_duration, fmt_dist, fmt_speed, bar


# ---------------------------------------------------------------------------
# Public helpers (used by report.py CLI)
# ---------------------------------------------------------------------------

def week_label(dt: datetime) -> str:
    """Return ISO week label, e.g. '2026-W08'."""
    iso = dt.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def session_filename(dt: datetime) -> str:
    return f"session_{dt.strftime('%Y-%m-%d_%H-%M')}.md"


# ---------------------------------------------------------------------------
# Private formatting helpers
# ---------------------------------------------------------------------------

def _fmt_duration(seconds: float | None) -> str:
    return fmt_duration(seconds, show_seconds=False)


def _fmt_dist(meters: float | None) -> str:
    return fmt_dist(meters)


def _fmt_speed(mps: float | None) -> str:
    return fmt_speed(mps)


def _bar(pct: float, width: int = 20) -> str:
    return bar(pct, width)


def _v(val, fmt: str | None = None, suffix: str = "") -> str:
    """Format optional value, returning em-dash if None."""
    if val is None:
        return "—"
    if fmt:
        return fmt.format(val) + suffix
    return str(val) + suffix


def _is_indoor(result: AnalysisResult) -> bool:
    sub = result.workout.session.sub_sport or ""
    return "indoor" in sub.lower()


def _avg(vals: list) -> float | None:
    clean = [v for v in vals if v is not None]
    return sum(clean) / len(clean) if clean else None


# ---------------------------------------------------------------------------
# Zone helpers
# ---------------------------------------------------------------------------

def _merge_zones(results: list[AnalysisResult]) -> list[ZoneDistribution]:
    """Sum seconds per Coggan zone across results, recalculate percentages."""
    totals: dict[str, int] = {name: 0 for _, _, name in COGGAN_ZONES}
    for result in results:
        for z in result.zones:
            totals[z.zone_name] = totals.get(z.zone_name, 0) + z.seconds

    grand_total = sum(totals.values())
    merged = []
    for lower_pct, upper_pct, name in COGGAN_ZONES:
        secs = totals.get(name, 0)
        pct = round(secs / grand_total * 100, 1) if grand_total else 0.0
        merged.append(ZoneDistribution(
            zone_name=name,
            lower_pct=lower_pct,
            upper_pct=upper_pct,
            seconds=secs,
            percent_of_ride=pct,
        ))
    return merged


def _zone_band_pcts(zones: list[ZoneDistribution]) -> tuple[float, float, float]:
    """(low%, mid%, high%) for Z1-Z2, Z3-Z4, Z5+."""
    low = sum(z.percent_of_ride for z in zones if z.zone_name[:2] in ("Z1", "Z2"))
    mid = sum(z.percent_of_ride for z in zones if z.zone_name[:2] in ("Z3", "Z4"))
    high = sum(z.percent_of_ride for z in zones if z.zone_name[:2] in ("Z5", "Z6", "Z7"))
    return low, mid, high


def _band_status(actual: float, lo: float, hi: float) -> str:
    if actual < lo:
        return "Low"
    if actual > hi:
        return "High"
    return "OK"


# ---------------------------------------------------------------------------
# Peak power
# ---------------------------------------------------------------------------

def _peak_powers(
    records: list[RecordPoint], ftp: int | None
) -> list[tuple[str, int, float | None]]:
    """Sliding-window best average power for standard durations."""
    powers = [r.power for r in records if r.power is not None]
    if not powers:
        return []

    result = []
    n_total = len(powers)
    for n, label in [
        (5, "5 sec"), (10, "10 sec"), (30, "30 sec"),
        (60, "1 min"), (300, "5 min"), (1200, "20 min"),
    ]:
        if n_total < n:
            continue
        win_sum = float(sum(powers[:n]))
        best = win_sum / n
        for i in range(1, n_total - n + 1):
            win_sum += powers[i + n - 1] - powers[i - 1]
            avg = win_sum / n
            if avg > best:
                best = avg
        best_w = round(best)
        pct = round(best_w / ftp * 100, 1) if ftp is not None and ftp > 0 else None
        result.append((label, best_w, pct))

    return result


# ---------------------------------------------------------------------------
# Interval execution analysis
# ---------------------------------------------------------------------------

def _interval_execution_section(ia: IntervalAnalysis, ftp: int) -> list[str]:
    """Render interval execution analysis as markdown lines."""
    lines: list[str] = ["## Interval Execution Analysis", ""]
    wi = ia.work_intervals
    n = len(wi)

    # Header: identify intervals and target range
    targets_match = all(
        w.target_low == wi[0].target_low and w.target_high == wi[0].target_high
        for w in wi
    )
    if targets_match:
        if wi[0].target_low != wi[0].target_high:
            tgt_str = f"{wi[0].target_low}–{wi[0].target_high} W"
        else:
            tgt_str = f"{wi[0].target_low} W"
        lines.append(f"**{n} work intervals** identified (target: {tgt_str})")
    else:
        lines.append(f"**{n} work intervals** identified (mixed targets)")
    lines.append("")

    # Per-interval compliance table
    has_hr = any(w.avg_heart_rate is not None for w in wi)

    header = ["Interval", "Time", "Avg W", "Target", "Deviation"]
    if has_hr:
        header.append("Avg HR")
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")

    for w in wi:
        status = "✓" if w.in_target else ("↑" if w.deviation_watts > 0 else "↓")
        if w.target_low != w.target_high:
            tgt = f"{w.target_low}–{w.target_high} W {status}"
        else:
            tgt = f"{w.target_low} W {status}"
        dev_str = f"{w.deviation_watts:+.0f} W ({w.deviation_pct:+.1f}%)"
        row = [
            f"Lap {w.lap_number + 1}",
            _fmt_duration(w.elapsed_time),
            f"{w.avg_power:.0f} W",
            tgt,
            dev_str,
        ]
        if has_hr:
            row.append(f"{w.avg_heart_rate} bpm" if w.avg_heart_rate else "—")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # Consistency & Fade
    lines.append("### Consistency & Fade")
    lines.append("")
    lines.append(
        f"- **Mean work power:** {ia.mean_work_power:.0f} W "
        f"({ia.mean_work_power / ftp * 100:.1f}% FTP)"
    )

    if ia.cv_pct < 2:
        cv_label = "Excellent"
    elif ia.cv_pct < 5:
        cv_label = "Good"
    else:
        cv_label = "Inconsistent"
    lines.append(f"- **Coefficient of variation:** {ia.cv_pct:.1f}% ({cv_label})")

    first_w = wi[0].avg_power
    last_w = wi[-1].avg_power
    if abs(ia.fade_pct) < 2:
        fade_label = "negligible"
    elif ia.fade_pct < -5:
        fade_label = "significant fade"
    elif ia.fade_pct < 0:
        fade_label = "mild fade"
    elif ia.fade_pct > 5:
        fade_label = "strong positive build"
    else:
        fade_label = "mild positive build"
    lines.append(
        f"- **Fade:** {ia.fade_pct:+.1f}% "
        f"({first_w:.0f} → {last_w:.0f} W) — {fade_label}"
    )

    lines.append(
        f"- **Target compliance:** {ia.compliance_pct:.0f}% of intervals within target "
        f"(mean deviation: {ia.mean_deviation_watts:.0f} W)"
    )

    # HR Cost (conditional)
    if ia.cardiac_drift_pct is not None:
        lines.append("")
        lines.append("### HR Cost")
        lines.append("")

        first_hr = wi[0].avg_heart_rate
        last_hr = next(
            w.avg_heart_rate for w in reversed(wi) if w.avg_heart_rate is not None
        )
        if abs(ia.cardiac_drift_pct) < 3:
            drift_label = "stable — good aerobic capacity at this intensity"
        elif ia.cardiac_drift_pct > 5:
            drift_label = "significant drift — approaching aerobic ceiling"
        elif ia.cardiac_drift_pct > 0:
            drift_label = "mild drift — normal for sustained threshold work"
        else:
            drift_label = "HR decrease — possible warmup effect or pacing adjustment"

        lines.append(
            f"- **Cardiac drift:** {ia.cardiac_drift_pct:+.1f}% "
            f"({first_hr} → {last_hr} bpm) — {drift_label}"
        )

        hr_ratios = [
            (w.avg_power / w.avg_heart_rate)
            for w in wi
            if w.avg_heart_rate and w.avg_heart_rate > 0
        ]
        if len(hr_ratios) >= 2:
            ratio_change = (hr_ratios[-1] - hr_ratios[0]) / hr_ratios[0] * 100
            lines.append(
                f"- **Power:HR ratio:** {hr_ratios[0]:.2f} → {hr_ratios[-1]:.2f} W/bpm "
                f"({ratio_change:+.1f}%)"
            )

    lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Session classification
# ---------------------------------------------------------------------------

@dataclass
class SessionClassification:
    session_type: str
    is_muddle: bool
    tss_status: str  # "OK", "Low", "High", "N/A"


def _lap_based_session_type(result: AnalysisResult) -> Optional[str]:
    """Classify session from lap structure when clear interval work exists.

    Checks lap power and duration against expected ranges per training type:
      VO2max / Hard : ≥ 110% FTP,  2–6 min per effort
      Threshold     : 90–110% FTP, 10–60 min per effort
      Sweet Spot    : 84–90% FTP,  10–90 min per effort

    Uses normalized_power when available, falling back to avg_power.
    Requires ≥ 2 matching laps before declaring a session type.
    Returns None when no clear interval structure is found, so the caller
    can fall back to IF-based classification.
    """
    if not result.ftp:
        return None
    ftp = result.ftp

    # (min_pct_ftp, max_pct_ftp, min_dur_s, max_dur_s, label)
    # Tempo checked before Sweet Spot: shorter intervals (5–15 min) at 76–88% FTP.
    # Sweet Spot requires ≥15 min sustained effort to distinguish from Tempo intervals.
    interval_profiles = [
        (1.10, float("inf"), 120,  360,  "VO2max / Hard"),
        (0.90, 1.10,         600, 3600,  "Threshold"),
        (0.76, 0.88,         300,  900,  "Tempo"),
        (0.84, 0.90,         900, 5400,  "Sweet Spot"),
    ]

    for min_pct, max_pct, min_dur, max_dur, label in interval_profiles:
        lo_w = ftp * min_pct
        hi_w = ftp * max_pct
        count = sum(
            1 for lap in result.workout.laps
            if (pwr := (lap.normalized_power or lap.avg_power)) is not None
            and lo_w <= pwr < hi_w
            and min_dur <= (lap.elapsed_time or 0.0) <= max_dur
        )
        if count >= 2:
            return label

    return None


def _classify_session(result: AnalysisResult) -> SessionClassification:
    IF = result.intensity_factor

    # Primary: derive session type from interval lap structure when possible.
    # Overall NP/IF is suppressed by recovery laps between efforts, making IF
    # alone unreliable for sessions built around short, hard intervals.
    session_type = _lap_based_session_type(result)

    if session_type is None:
        # Fallback: IF-based classification for unstructured / steady-state rides.
        if IF is None:
            session_type = "Unknown"
        elif IF < 0.60:
            session_type = "Recovery"
        elif IF < 0.73:
            session_type = "Endurance"
        elif IF < 0.80:
            session_type = "Tempo"
        elif IF < 0.90:
            session_type = "Sweet Spot"
        elif IF < 1.05:
            session_type = "Threshold"
        else:
            session_type = "VO2max / Hard"

    # Muddle detection
    is_muddle = False
    if result.zones and IF is not None:
        z3 = next((z.percent_of_ride for z in result.zones if z.zone_name.startswith("Z3")), 0.0)
        z4 = next((z.percent_of_ride for z in result.zones if z.zone_name.startswith("Z4")), 0.0)
        is_muddle = (
            session_type != "Tempo"
            and z3 + z4 > 40 and z4 < 25 and z3 > 20 and 0.78 <= IF <= 0.92
        )

    # TSS status
    tss_status = "N/A"
    tss = result.tss
    if tss is not None:
        ranges = {
            "Recovery": (0, 40),
            "Endurance": (40, 80),
            "Tempo": (60, 100),
            "Sweet Spot": (70, 100),
            "Threshold": (80, 120),
            "VO2max / Hard": (60, 100),
        }
        if session_type in ranges:
            lo, hi = ranges[session_type]
            tss_status = "Low" if tss < lo else "High" if tss > hi else "OK"

    return SessionClassification(
        session_type=session_type,
        is_muddle=is_muddle,
        tss_status=tss_status,
    )


def _session_commentary(result: AnalysisResult, cls: SessionClassification, indoor: bool = False) -> str:
    IF_str = f"{result.intensity_factor:.3f}" if result.intensity_factor is not None else "N/A"
    tss_str = f"{result.tss:.0f}" if result.tss is not None else "N/A"

    # Dominant zones (top 2 by time, ≥10%)
    dominant = []
    if result.zones:
        for z in sorted(result.zones, key=lambda x: x.seconds, reverse=True):
            if z.percent_of_ride >= 10:
                dominant.append(z.zone_name)
            if len(dominant) == 2:
                break
    zone_text = " and ".join(dominant) if dominant else "mixed zones"

    if cls.tss_status == "OK":
        tss_verdict = f"TSS of {tss_str} is within the healthy range."
    elif cls.tss_status in ("Low", "High"):
        tss_verdict = f"TSS of {tss_str} is {cls.tss_status.lower()} for a {cls.session_type} session."
    else:
        tss_verdict = "TSS not calculated (no FTP set)."

    para = (
        f"This was a **{cls.session_type}** session (IF {IF_str}), with time concentrated in "
        f"{zone_text}. {tss_verdict}"
    )

    warnings = []
    if cls.is_muddle:
        warnings.append(
            "**Moderate muddle detected** — significant time in Z3 without reaching a clean "
            "threshold stimulus. Either back off to true Z2 endurance or commit to focused "
            "Z4 threshold work."
        )
    if cls.tss_status == "High":
        warnings.append(
            f"**TSS elevated** for a {cls.session_type} session — monitor cumulative fatigue."
        )
    elif cls.tss_status == "Low":
        warnings.append(f"**TSS lower than expected** for a {cls.session_type} session.")

    if indoor and result.workout.session.avg_heart_rate is None:
        warnings.append(
            "**No HR data** — for indoor sessions HR is typically 3–10 bpm lower than "
            "outdoor at the same power (gap is larger early season, smaller late summer)."
        )

    parts = [para]
    if warnings:
        parts.append("### Warnings\n" + "\n".join(f"- {w}" for w in warnings))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Per-session one-liner for weekly summary
# ---------------------------------------------------------------------------

def _session_one_liner(result: AnalysisResult, cls: SessionClassification, filename: str) -> str:
    dt = result.workout.session.start_time
    date_str = dt.strftime("%Y-%m-%d") if dt else "Unknown"
    dur = _fmt_duration(result.workout.session.timer_time or result.workout.session.elapsed_time)

    details = []
    if result.zones:
        z2_pct = next((z.percent_of_ride for z in result.zones if z.zone_name.startswith("Z2")), 0.0)
        z3_pct = next((z.percent_of_ride for z in result.zones if z.zone_name.startswith("Z3")), 0.0)
        z4_pct = next((z.percent_of_ride for z in result.zones if z.zone_name.startswith("Z4")), 0.0)
        if z2_pct >= 50:
            zone_str = f"{z2_pct:.0f}% Z2"
            if z3_pct >= 5:
                zone_str += f" / {z3_pct:.0f}% Z3"
            details.append(zone_str)
        elif z4_pct >= 30:
            details.append(f"{z4_pct:.0f}% Z4")
        elif z3_pct >= 30:
            details.append(f"{z3_pct:.0f}% Z3")

    if result.variability_index is not None:
        details.append(f"VI {result.variability_index:.3f}")
    if result.intensity_factor is not None:
        details.append(f"IF {result.intensity_factor:.3f}")

    detail_str = f" ({', '.join(details)})" if details else ""
    return f"- [{date_str}]({filename}) — {dur} {cls.session_type}{detail_str}."


# ---------------------------------------------------------------------------
# Critique & Insights for weekly summary
# ---------------------------------------------------------------------------

def _critique_and_insights(
    results: list[AnalysisResult],
    classifications: list[SessionClassification],
) -> str:
    points = []

    # 1. Zone execution quality
    if not any(c.is_muddle for c in classifications):
        z2_pcts = [
            next((z.percent_of_ride for z in r.zones if z.zone_name.startswith("Z2")), 0.0)
            for r in results if r.zones
        ]
        if z2_pcts and sum(z2_pcts) / len(z2_pcts) > 85:
            avg_z2 = sum(z2_pcts) / len(z2_pcts)
            points.append(
                f"**Clean Z2 execution** — average {avg_z2:.0f}% Z2 across sessions, no muddle risk."
            )
    else:
        muddle_count = sum(1 for c in classifications if c.is_muddle)
        points.append(
            f"**{muddle_count} session{'s' if muddle_count > 1 else ''} drifted into muddle territory** — "
            "consider backing off to clean Z2 or committing to structured threshold work."
        )

    # 2. Pedaling dynamics asymmetry
    all_lte, all_rte, all_left = [], [], []
    for r in results:
        all_lte += [rec.left_torque_effectiveness for rec in r.workout.records if rec.left_torque_effectiveness is not None]
        all_rte += [rec.right_torque_effectiveness for rec in r.workout.records if rec.right_torque_effectiveness is not None]
        all_left += [rec.left_pct for rec in r.workout.records if rec.left_pct is not None]
    if all_lte and all_rte:
        avg_lte = sum(all_lte) / len(all_lte)
        avg_rte = sum(all_rte) / len(all_rte)
        gap = avg_rte - avg_lte
        if gap > 3:
            bal_str = ""
            if all_left:
                avg_l = sum(all_left) / len(all_left)
                bal_str = f" ({avg_l:.0f}/{100 - avg_l:.0f}% L/R balance)"
            points.append(
                f"**Right/left torque effectiveness gap**: right {avg_rte:.0f}% vs left {avg_lte:.0f}%"
                f"{bal_str} — consistent {gap:.0f} pp asymmetry. Worth monitoring as intensity increases."
            )

    # 3. Pacing consistency
    vi_vals = [r.variability_index for r in results if r.variability_index is not None]
    if vi_vals:
        avg_vi = sum(vi_vals) / len(vi_vals)
        all_indoor = all(_is_indoor(r) for r in results if r.variability_index is not None)

        if all_indoor:
            if avg_vi < 1.05:
                points.append(
                    f"**VI in expected range for indoor conditions** — average VI {avg_vi:.3f} "
                    "(no terrain or wind variation); consistent output still requires discipline."
                )
            elif avg_vi > 1.08:
                points.append(
                    f"**Notable pacing variability for indoor riding** — average VI {avg_vi:.3f}; "
                    "aim for VI ≤ 1.05 in controlled indoor conditions."
                )
        else:
            if avg_vi < 1.05:
                points.append(
                    f"**Excellent pacing consistency** — average VI {avg_vi:.3f}, "
                    "reflecting disciplined steady-state execution outdoors."
                )
            elif avg_vi > 1.10:
                points.append(
                    f"**High pacing variability** — average VI {avg_vi:.3f}; "
                    "aim for VI ≤ 1.05 on flat terrain, ≤ 1.10 on hilly routes."
                )

    # 4. Volume and frequency
    dates = sorted(
        r.workout.session.start_time.date()
        for r in results if r.workout.session.start_time
    )
    if dates:
        span_days = (dates[-1] - dates[0]).days + 1
        rest_days = span_days - len(dates)
        total_tss = sum(r.tss or 0 for r in results)
        total_hours = sum(
            (r.workout.session.timer_time or r.workout.session.elapsed_time or 0)
            for r in results
        ) / 3600
        if rest_days == 0 and len(dates) >= 5:
            points.append(
                f"**No rest days** across {span_days} consecutive days "
                f"({total_tss:.0f} TSS, {total_hours:.1f}h) — "
                "ensure adequate recovery before adding intensity next week."
            )
        else:
            points.append(
                f"**{len(dates)} sessions across {span_days} days** with {rest_days} rest day{'s' if rest_days != 1 else ''} "
                f"({total_tss:.0f} TSS, {total_hours:.1f}h total)."
            )

    if not points:
        points.append("Training execution was consistent with no significant issues to flag.")

    return "\n".join(f"- {p}" for p in points)


# ---------------------------------------------------------------------------
# Session report
# ---------------------------------------------------------------------------

def generate_session_report(result: AnalysisResult, source_filename: str) -> str:
    s = result.workout.session
    records = result.workout.records
    laps = result.workout.laps
    dt = s.start_time
    indoor = _is_indoor(result)
    venue = "Indoor" if indoor else "Outdoor"
    header_dt = dt.strftime("%Y-%m-%d %H:%M") if dt else "Unknown"

    lines: list[str] = [f"# Session Report — {header_dt} [{venue}]", ""]
    lines += [f"*Source: `{source_filename}`*", ""]

    # Session Stats
    lines += ["## Session Stats", ""]
    lines += ["| Field | Value |", "|---|---|"]
    lines.append(f"| Date | {dt.strftime('%Y-%m-%d %H:%M') if dt else '—'} |")
    lines.append(f"| Venue | {venue} |")
    lines.append(f"| Sport | {_v(s.sport)}{f' / {s.sub_sport}' if s.sub_sport else ''} |")
    lines.append(f"| Elapsed Duration | {_fmt_duration(s.elapsed_time)} |")
    lines.append(f"| Timer Duration | {_fmt_duration(s.timer_time)} |")
    lines.append(f"| Distance | {_fmt_dist(s.distance)} |")
    lines.append(f"| Calories | {_v(s.calories, suffix=' kcal')} |")
    lines.append(f"| Total Work | {_v(s.total_work_kj, fmt='{:.0f}', suffix=' kJ')} |")
    lines.append(f"| Ascent | {_v(s.ascent, fmt='{:.0f}', suffix=' m')} |")
    if s.avg_temperature is not None:
        lines.append(
            f"| Temperature | avg {s.avg_temperature:.0f}°C"
            f"  (min {_v(s.min_temperature, fmt='{:.0f}', suffix='°C')},"
            f" max {_v(s.max_temperature, fmt='{:.0f}', suffix='°C')}) |"
        )
    lines.append("")

    # Power Summary
    lines += ["## Power Summary", ""]
    lines += ["| Metric | Value |", "|---|---|"]
    lines.append(f"| Avg Power | {_v(s.avg_power, fmt='{:.0f}', suffix=' W')} |")
    lines.append(f"| Max Power | {_v(s.max_power, suffix=' W')} |")
    lines.append(f"| Normalized Power (NP) | {_v(result.normalized_power, fmt='{:.0f}', suffix=' W')} |")
    lines.append(f"| Variability Index (VI) | {_v(result.variability_index, fmt='{:.3f}')} |")
    lines.append(f"| Intensity Factor (IF) | {_v(result.intensity_factor, fmt='{:.3f}')} |")
    lines.append(f"| TSS | {_v(result.tss, fmt='{:.1f}')} |")
    lines.append(f"| FTP | {_v(result.ftp, suffix=' W')} |")
    if result.weight and result.weight > 0:
        if s.avg_power:
            lines.append(f"| Avg W/kg | {s.avg_power / result.weight:.2f} W/kg |")
        if result.normalized_power:
            lines.append(f"| NP W/kg | {result.normalized_power / result.weight:.2f} W/kg |")
    lines.append("")

    # Heart Rate (conditional)
    if s.avg_heart_rate or s.max_heart_rate:
        lines += ["## Heart Rate", ""]
        lines += ["| Metric | Value |", "|---|---|"]
        lines.append(f"| Avg HR | {_v(s.avg_heart_rate, suffix=' bpm')} |")
        lines.append(f"| Max HR | {_v(s.max_heart_rate, suffix=' bpm')} |")
        if indoor:
            lines.append(
                "| *Indoor note* | *HR typically 3–10 bpm lower than outdoor at same power* |"
            )
        lines.append("")

    # Cadence & Speed (conditional)
    cad_vals = [r.cadence for r in records if r.cadence is not None and r.cadence > 0]
    spd_vals = [r.speed for r in records if r.speed is not None]
    if cad_vals or spd_vals:
        lines += ["## Cadence & Speed", ""]
        lines += ["| Metric | Value |", "|---|---|"]
        if cad_vals:
            lines.append(f"| Avg Cadence | {sum(cad_vals) / len(cad_vals):.0f} rpm |")
            lines.append(f"| Max Cadence | {max(cad_vals)} rpm |")
        if spd_vals:
            lines.append(f"| Avg Speed | {_fmt_speed(sum(spd_vals) / len(spd_vals))} |")
            lines.append(f"| Max Speed | {_fmt_speed(max(spd_vals))} |")
        lines.append("")

    # Pedaling Dynamics (conditional — requires dual-sided power meter)
    lr_vals = [r.left_pct for r in records if r.left_pct is not None]
    lte_vals = [r.left_torque_effectiveness for r in records if r.left_torque_effectiveness is not None]
    rte_vals = [r.right_torque_effectiveness for r in records if r.right_torque_effectiveness is not None]
    lps_vals = [r.left_pedal_smoothness for r in records if r.left_pedal_smoothness is not None]
    rps_vals = [r.right_pedal_smoothness for r in records if r.right_pedal_smoothness is not None]
    if lr_vals or lte_vals:
        lines += ["## Pedaling Dynamics", ""]
        lines += ["| Metric | Left | Right |", "|---|---|---|"]
        if lr_vals:
            avg_left = sum(lr_vals) / len(lr_vals)
            lines.append(f"| Power Balance | {avg_left:.1f}% | {100 - avg_left:.1f}% |")
        if lte_vals and rte_vals:
            lines.append(
                f"| Torque Effectiveness | {_avg(lte_vals):.1f}% | {_avg(rte_vals):.1f}% |"
            )
        if lps_vals and rps_vals:
            lines.append(
                f"| Pedal Smoothness | {_avg(lps_vals):.1f}% | {_avg(rps_vals):.1f}% |"
            )
        lines.append("")

    # Peak Power Durations
    peaks = _peak_powers(records, result.ftp)
    if peaks:
        lines += ["## Peak Power Durations", ""]
        if result.weight and result.weight > 0:
            lines += ["| Duration | Best Power | % FTP | W/kg |", "|---|---|---|---|"]
            for label, watts, pct_ftp in peaks:
                pct_str = f"{pct_ftp:.1f}%" if pct_ftp is not None else "—"
                lines.append(f"| {label} | {watts} W | {pct_str} | {watts / result.weight:.2f} |")
        else:
            lines += ["| Duration | Best Power | % FTP |", "|---|---|---|"]
            for label, watts, pct_ftp in peaks:
                pct_str = f"{pct_ftp:.1f}%" if pct_ftp is not None else "—"
                lines.append(f"| {label} | {watts} W | {pct_str} |")
        lines.append("")

    # Laps / Intervals
    if laps:
        has_targets = any(lap.target_power_low is not None for lap in laps)
        has_hr = any(lap.avg_heart_rate is not None for lap in laps)
        has_dist = any(lap.distance is not None and lap.distance > 0 for lap in laps)

        header_cols = ["Lap", "Time", "Avg W", "NP", "kJ"]
        sep_cols = ["---"] * len(header_cols)
        if has_targets:
            header_cols.append("Target")
            sep_cols.append("---")
        if has_hr:
            header_cols += ["Avg HR", "Max HR"]
            sep_cols += ["---", "---"]
        header_cols += ["Avg Cad", "Temp"]
        sep_cols += ["---", "---"]
        if has_dist:
            header_cols.append("Distance")
            sep_cols.append("---")

        lines += ["## Laps / Intervals", ""]
        lines.append("| " + " | ".join(header_cols) + " |")
        lines.append("| " + " | ".join(sep_cols) + " |")

        for lap in laps:
            # Compliance indicator for target power
            if has_targets and lap.target_power_low is not None and lap.avg_power is not None:
                if lap.target_power_high is not None:
                    if lap.avg_power < lap.target_power_low:
                        target_str = f"{lap.target_power_low}–{lap.target_power_high} W ↓"
                    elif lap.avg_power > lap.target_power_high:
                        target_str = f"{lap.target_power_low}–{lap.target_power_high} W ↑"
                    else:
                        target_str = f"{lap.target_power_low}–{lap.target_power_high} W ✓"
                else:
                    diff = lap.avg_power - lap.target_power_low
                    if diff < -5:
                        target_str = f"{lap.target_power_low} W ↓"
                    elif diff > 5:
                        target_str = f"{lap.target_power_low} W ↑"
                    else:
                        target_str = f"{lap.target_power_low} W ✓"
            elif has_targets:
                target_str = "—"

            row = [
                str(lap.lap_number + 1),
                _fmt_duration(lap.elapsed_time),
                _v(lap.avg_power, fmt="{:.0f}", suffix=" W"),
                _v(lap.normalized_power, fmt="{:.0f}", suffix=" W"),
                _v(lap.total_work_kj, fmt="{:.0f}", suffix=" kJ"),
            ]
            if has_targets:
                row.append(target_str)
            if has_hr:
                row += [
                    _v(lap.avg_heart_rate, suffix=" bpm"),
                    _v(lap.max_heart_rate, suffix=" bpm"),
                ]
            row += [
                _v(lap.avg_cadence, suffix=" rpm"),
                _v(lap.avg_temperature, fmt="{:.0f}", suffix="°C"),
            ]
            if has_dist:
                row.append(_fmt_dist(lap.distance))

            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    # Interval Execution Analysis (structured workouts only)
    if result.interval_analysis and result.ftp:
        lines += _interval_execution_section(result.interval_analysis, result.ftp)

    # Power Zone Breakdown
    if result.zones:
        lines += ["## Power Zone Breakdown", ""]
        lines += ["| Zone | Range | Time | % |", "|---|---|---|---|"]
        ftp = result.ftp or 0
        for z in result.zones:
            lo_w = f"{z.lower_pct * ftp:.0f} W"
            hi_w = "∞" if z.upper_pct == float("inf") else f"{z.upper_pct * ftp:.0f} W"
            lines.append(
                f"| {z.zone_name} | {lo_w}–{hi_w} | {_fmt_duration(z.seconds)} | {z.percent_of_ride:.1f}% |"
            )
        lines.append("")
        lines.append("```")
        for z in result.zones:
            lines.append(f"{z.zone_name:<22} {_bar(z.percent_of_ride)} {z.percent_of_ride:5.1f}%")
        lines.append("```")
        lines.append("")

    # Session Commentary
    cls = _classify_session(result)
    lines += ["## Session Commentary", ""]
    lines.append(_session_commentary(result, cls, indoor=indoor))
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Code / data consistency observations (written to global code_improvements.md)
# ---------------------------------------------------------------------------

def collect_code_observations(results: list[AnalysisResult], week_label: str) -> list[str]:
    """Return data/model consistency notes for a processed week.

    These are surfaced to a global file rather than the training report because
    they describe classifier thresholds, parsing edge cases, or sensor gaps —
    not the athlete's training execution.
    """
    obs = []

    # Missing HR across all sessions
    no_hr = sum(1 for r in results if r.workout.session.avg_heart_rate is None)
    if no_hr == len(results) and len(results) > 1:
        obs.append(
            f"**No HR data in any session** ({week_label}): HR sensor was not recording. "
            f"HR context is unavailable for fatigue and intensity assessment this week."
        )

    return obs


# ---------------------------------------------------------------------------
# Weekly summary
# ---------------------------------------------------------------------------

def _weekly_commentary(
    results: list[AnalysisResult],
    week_label: str,
    merged_zones: list[ZoneDistribution],
) -> str:
    n = len(results)
    total_tss = sum((r.tss or 0) for r in results)
    total_dur = sum(
        (r.workout.session.timer_time or r.workout.session.elapsed_time or 0)
        for r in results
    )

    # Dominant session type
    type_counts: dict[str, int] = {}
    classifications = [_classify_session(r) for r in results]
    for c in classifications:
        type_counts[c.session_type] = type_counts.get(c.session_type, 0) + 1
    dominant_type = max(type_counts, key=type_counts.__getitem__) if type_counts else "Unknown"

    hours = total_dur / 3600
    para1 = (
        f"Week {week_label} comprised **{n} session{'s' if n != 1 else ''}** "
        f"totalling **{total_tss:.0f} TSS** across {hours:.1f} hours of riding. "
        f"The dominant session type was **{dominant_type}**."
    )

    # Zone alignment comment
    low, mid, high = _zone_band_pcts(merged_zones) if merged_zones else (0.0, 0.0, 0.0)
    if low < 55:
        zone_comment = (
            f"Low-intensity volume (Z1-Z2) was {low:.0f}% — below the 60–70% pyramidal target. "
            "Consider adding more aerobic base work to the next week."
        )
    elif high > 12:
        zone_comment = (
            f"High-intensity volume (Z5+) was {high:.0f}% — above the 5–10% target. "
            "Ensure adequate recovery between hard efforts."
        )
    else:
        zone_comment = (
            f"Zone distribution (Z1-Z2: {low:.0f}%, Z3-Z4: {mid:.0f}%, Z5+: {high:.0f}%) "
            "is broadly in line with pyramidal training targets."
        )

    warnings = []
    muddle_sessions = [c for c in classifications if c.is_muddle]
    if muddle_sessions:
        warnings.append(
            f"**{len(muddle_sessions)} session{'s' if len(muddle_sessions) > 1 else ''} flagged "
            "as moderate muddle** — time in the grey zone (Z3) without reaching threshold stimulus."
        )
    overreach = [r for r in results if r.tss and r.tss > 150]
    if overreach:
        warnings.append(
            f"**{len(overreach)} session{'s' if len(overreach) > 1 else ''} with TSS > 150** — "
            "high individual session load; monitor recovery closely."
        )

    text = para1 + "\n\n" + zone_comment
    if warnings:
        text += "\n\n### Warnings\n" + "\n".join(f"- {w}" for w in warnings)
    return text


def _fitness_section(metrics: FitnessMetrics) -> list[str]:
    """Build the Fitness & Fatigue (PMC) section lines for a weekly report."""
    c = metrics.current
    w = metrics.one_week_ago

    def _delta(now: float, prev: float) -> str:
        d = now - prev
        return f"+{d:.1f}" if d >= 0 else f"{d:.1f}"

    lines: list[str] = ["## Fitness & Fatigue (PMC)", ""]
    lines += ["| Metric | 7 Days Ago | End of Week | Δ |", "|---|---|---|---|"]
    lines.append(f"| CTL (Fitness) | {w.ctl:.1f} | {c.ctl:.1f} | {_delta(c.ctl, w.ctl)} |")
    lines.append(f"| ATL (Fatigue) | {w.atl:.1f} | {c.atl:.1f} | {_delta(c.atl, w.atl)} |")
    lines.append(
        f"| TSB (Form) | {w.tsb:+.1f} | {c.tsb:+.1f} | {_delta(c.tsb, w.tsb)} |"
    )
    lines.append("")
    lines.append(
        f"**Form:** {c.form_label} (TSB {c.tsb:+.1f})  "
        f"**Weekly CTL ramp:** {metrics.ctl_weekly_ramp:+.1f} pts/week ({metrics.ramp_label})"
    )
    if metrics.history_days < CTL_TC:
        lines.append(
            f"*Note: CTL seeded from {metrics.history_days} days of history "
            f"— values stabilise after {CTL_TC}+ days. Run `report.py block` to bootstrap.*"
        )
    lines.append("")
    return lines


def generate_weekly_summary(
    results: list[AnalysisResult],
    week_label: str,
    session_filenames: list[str] | None = None,
    fitness_metrics: FitnessMetrics | None = None,
) -> str:
    if not results:
        return f"# Weekly Summary — {week_label}\n\nNo sessions found.\n"

    ftp = next((r.ftp for r in results if r.ftp), None)

    dates = [r.workout.session.start_time for r in results if r.workout.session.start_time]
    if len(dates) >= 2:
        period = f"{min(dates).strftime('%Y-%m-%d')} – {max(dates).strftime('%Y-%m-%d')}"
    elif dates:
        period = dates[0].strftime("%Y-%m-%d")
    else:
        period = week_label

    # Aggregates
    total_tss = sum((r.tss or 0) for r in results)
    total_dur = sum(
        (r.workout.session.timer_time or r.workout.session.elapsed_time or 0)
        for r in results
    )
    total_dist = sum(
        (r.workout.session.distance or 0) for r in results if not _is_indoor(r)
    )
    total_ascent = sum(
        (r.workout.session.ascent or 0) for r in results
    )
    if_vals = [r.intensity_factor for r in results if r.intensity_factor is not None]
    np_vals = [r.normalized_power for r in results if r.normalized_power is not None]
    avg_IF = sum(if_vals) / len(if_vals) if if_vals else None
    avg_NP = sum(np_vals) / len(np_vals) if np_vals else None

    lines: list[str] = [f"# Weekly Summary — {week_label}", ""]
    lines.append(f"*Period: {period}*")
    if ftp:
        lines.append(f"*FTP: {ftp} W*")
    lines.append("")

    # Week at a Glance
    lines += ["## Week at a Glance", ""]
    lines += ["| Metric | Value |", "|---|---|"]
    lines.append(f"| Sessions | {len(results)} |")
    lines.append(f"| Total TSS | {total_tss:.0f} |")
    lines.append(f"| Total Duration | {_fmt_duration(total_dur)} |")
    lines.append(f"| Total Distance | {_fmt_dist(total_dist) if total_dist else '—'} |")
    if total_ascent > 0:
        lines.append(f"| Total Ascent | {total_ascent:.0f} m |")
    lines.append(f"| Avg IF | {f'{avg_IF:.3f}' if avg_IF is not None else '—'} |")
    lines.append(f"| Avg NP | {f'{avg_NP:.0f} W' if avg_NP is not None else '—'} |")
    weight = next((r.weight for r in results if r.weight is not None and r.weight > 0), None)
    if weight and avg_NP is not None:
        lines.append(f"| Avg NP W/kg | {avg_NP / weight:.2f} W/kg |")
    lines.append("")

    # Fitness & Fatigue (PMC)
    if fitness_metrics is not None:
        lines += _fitness_section(fitness_metrics)

    # Sort results and filenames together chronologically
    filenames = session_filenames or [""] * len(results)
    paired = sorted(
        zip(results, filenames),
        key=lambda x: x[0].workout.session.start_time or datetime.min,
    )
    classifications = [_classify_session(r) for r, _ in paired]

    # Sessions table
    lines += ["## Sessions", ""]
    lines += ["| Date | Type | Duration | NP | IF | TSS | Flags |", "|---|---|---|---|---|---|---|"]
    for (r, _), cls in zip(paired, classifications):
        dt = r.workout.session.start_time
        date_str = dt.strftime("%Y-%m-%d") if dt else "—"
        dur = _fmt_duration(r.workout.session.timer_time or r.workout.session.elapsed_time)
        np_str = f"{r.normalized_power:.0f} W" if r.normalized_power is not None else "—"
        if_str = f"{r.intensity_factor:.3f}" if r.intensity_factor is not None else "—"
        tss_str = f"{r.tss:.0f}" if r.tss is not None else "—"
        flags = []
        if cls.is_muddle:
            flags.append("muddle")
        if cls.tss_status not in ("OK", "N/A"):
            flags.append(f"TSS {cls.tss_status.lower()}")
        flags_str = ", ".join(flags) if flags else "—"
        lines.append(
            f"| {date_str} | {cls.session_type} | {dur} | {np_str} | {if_str} | {tss_str} | {flags_str} |"
        )
    lines.append("")

    # Session Descriptions (linked, one-liner each)
    if session_filenames:
        lines += ["## Session Descriptions", ""]
        for (r, fname), cls in zip(paired, classifications):
            lines.append(_session_one_liner(r, cls, fname))
        lines.append("")

    # Combined Zone Distribution
    merged = _merge_zones(results)
    if any(z.seconds > 0 for z in merged):
        lines += ["## Combined Zone Distribution", ""]
        lines += ["| Zone | Time | % |", "|---|---|---|"]
        for z in merged:
            lines.append(f"| {z.zone_name} | {_fmt_duration(z.seconds)} | {z.percent_of_ride:.1f}% |")
        lines.append("")
        lines.append("```")
        for z in merged:
            lines.append(f"{z.zone_name:<22} {_bar(z.percent_of_ride)} {z.percent_of_ride:5.1f}%")
        lines.append("```")
        lines.append("")

        # Training Model Alignment
        low, mid, high = _zone_band_pcts(merged)
        lines += ["## Training Model Alignment", ""]
        lines += ["| Band | Target | Actual | Status |", "|---|---|---|---|"]
        lines.append(f"| Z1-Z2 (Low intensity) | 60–70% | {low:.1f}% | {_band_status(low, 60, 70)} |")
        lines.append(f"| Z3-Z4 (Mid intensity) | 20–25% | {mid:.1f}% | {_band_status(mid, 20, 25)} |")
        lines.append(f"| Z5+ (High intensity) | 5–10% | {high:.1f}% | {_band_status(high, 5, 10)} |")
        lines.append("")

    # Critique & Insights
    lines += ["## Critique & Insights", ""]
    lines.append(_critique_and_insights([r for r, _ in paired], classifications))
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Block analysis
# ---------------------------------------------------------------------------

def generate_block_analysis(
    weeks: list[list[AnalysisResult]],
    week_labels: list[str],
    weekly_snapshots: list[FitnessSnapshot] | None = None,
) -> str:
    if not weeks:
        return "# Block Analysis\n\nNo data found.\n"

    ftp = None
    for week in weeks:
        for r in week:
            if r.ftp:
                ftp = r.ftp
                break
        if ftp:
            break

    n_weeks = len(weeks)
    lines: list[str] = [f"# Block Analysis — {n_weeks} Week{'s' if n_weeks != 1 else ''}", ""]
    if ftp:
        lines.append(f"*FTP: {ftp} W*")
    lines.append(f"*Weeks: {', '.join(week_labels)}*")
    lines.append("")

    # Per-week statistics
    week_stats = []
    for label, week in zip(week_labels, weeks):
        total_tss = sum((r.tss or 0) for r in week)
        total_dur = sum(
            (r.workout.session.timer_time or r.workout.session.elapsed_time or 0)
            for r in week
        )
        if_vals = [r.intensity_factor for r in week if r.intensity_factor is not None]
        avg_IF = sum(if_vals) / len(if_vals) if if_vals else None
        np_vals = [r.normalized_power for r in week if r.normalized_power is not None]
        avg_NP = sum(np_vals) / len(np_vals) if np_vals else None
        vi_vals = [r.variability_index for r in week if r.variability_index is not None]
        avg_VI = sum(vi_vals) / len(vi_vals) if vi_vals else None

        type_counts: dict[str, int] = {}
        for r in week:
            cls = _classify_session(r)
            type_counts[cls.session_type] = type_counts.get(cls.session_type, 0) + 1
        dominant = max(type_counts, key=type_counts.__getitem__) if type_counts else "—"

        merged = _merge_zones(week)
        low, mid, high = _zone_band_pcts(merged)

        week_stats.append({
            "label": label,
            "n": len(week),
            "total_tss": total_tss,
            "total_hours": total_dur / 3600,
            "avg_IF": avg_IF,
            "avg_NP": avg_NP,
            "avg_VI": avg_VI,
            "dominant_type": dominant,
            "low_pct": low,
            "mid_pct": mid,
            "high_pct": high,
            "merged_zones": merged,
        })

    # Week-by-Week Overview
    lines += ["## Week-by-Week Overview", ""]
    lines += [
        "| Week | Sessions | Total TSS | Total Hours | Avg IF | Dominant Type |",
        "|---|---|---|---|---|---|",
    ]
    for ws in week_stats:
        avg_if_str = f"{ws['avg_IF']:.3f}" if ws["avg_IF"] is not None else "—"
        lines.append(
            f"| {ws['label']} | {ws['n']} | {ws['total_tss']:.0f} | "
            f"{ws['total_hours']:.1f}h | {avg_if_str} | {ws['dominant_type']} |"
        )
    lines.append("")

    # Power Metric Trends
    lines += ["## Power Metric Trends", ""]
    lines += ["| Week | Avg NP | Avg IF | Avg VI |", "|---|---|---|---|"]
    for ws in week_stats:
        np_str = f"{ws['avg_NP']:.0f} W" if ws["avg_NP"] is not None else "—"
        if_str = f"{ws['avg_IF']:.3f}" if ws["avg_IF"] is not None else "—"
        vi_str = f"{ws['avg_VI']:.3f}" if ws["avg_VI"] is not None else "—"
        lines.append(f"| {ws['label']} | {np_str} | {if_str} | {vi_str} |")
    lines.append("")

    # Zone Distribution Trends
    lines += ["## Zone Distribution Trends", ""]
    lines += ["| Week | Z1-Z2 (Low) | Z3-Z4 (Mid) | Z5+ (High) |", "|---|---|---|---|"]
    for ws in week_stats:
        lines.append(
            f"| {ws['label']} | {ws['low_pct']:.1f}% | {ws['mid_pct']:.1f}% | {ws['high_pct']:.1f}% |"
        )
    lines.append("")

    # Phase Classification
    all_results = [r for week in weeks for r in week]
    all_if_vals = [r.intensity_factor for r in all_results if r.intensity_factor is not None]
    block_avg_IF = sum(all_if_vals) / len(all_if_vals) if all_if_vals else None

    tss_by_week = [ws["total_tss"] for ws in week_stats]
    if block_avg_IF is None:
        phase = "Unknown (no FTP set)"
    elif block_avg_IF < 0.80:
        phase = "Base / Aerobic Development"
    elif block_avg_IF < 0.90:
        phase = "Build / Tempo-SST"
    else:
        phase = "Peak / Threshold"

    tss_trend = ""
    if len(tss_by_week) >= 3:
        n = len(tss_by_week)
        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        y_mean = sum(tss_by_week) / n
        ss_xy = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, tss_by_week))
        ss_xx = sum((x - x_mean) ** 2 for x in x_vals)
        ss_yy = sum((y - y_mean) ** 2 for y in tss_by_week)
        slope = ss_xy / ss_xx if ss_xx else 0
        r_sq = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_xx and ss_yy else 0
        if slope > 0 and r_sq > 0.5:
            tss_trend = " Progressive loading detected."
        deload = tss_by_week[-1] < tss_by_week[-2] * 0.7
        if deload:
            tss_trend = " Deload present (final week TSS < 70% of previous)."
    elif len(tss_by_week) == 2:
        if tss_by_week[1] > tss_by_week[0]:
            tss_trend = " Progressive loading detected."
        elif tss_by_week[-1] < tss_by_week[-2] * 0.7:
            tss_trend = " Deload present (final week TSS < 70% of previous)."

    lines += ["## Phase Classification", ""]
    lines.append(f"**Phase:** {phase}{tss_trend}")
    if block_avg_IF is not None:
        lines.append(f"Block average IF: {block_avg_IF:.3f}")
    lines.append("")

    # Warnings
    warnings = []
    muddle_count = sum(
        1 for week in weeks for r in week if _classify_session(r).is_muddle
    )
    if muddle_count:
        warnings.append(
            f"**{muddle_count} muddle session{'s' if muddle_count > 1 else ''}** across the block — "
            "time spent in the grey zone without clear training stimulus."
        )

    all_low = [ws["low_pct"] for ws in week_stats]
    if all_low and all(lo < 55 for lo in all_low):
        warnings.append(
            "**Consistently low Z1-Z2 volume** across all weeks — "
            f"averaging {sum(all_low) / len(all_low):.0f}% vs 60–70% target."
        )

    all_high = [ws["high_pct"] for ws in week_stats]
    if all_high and all(hi > 12 for hi in all_high):
        warnings.append(
            "**Consistently elevated high-intensity volume** (Z5+) — "
            f"averaging {sum(all_high) / len(all_high):.0f}% vs 5–10% target."
        )

    overreach_weeks = [ws["label"] for ws in week_stats if ws["total_tss"] > 600]
    if overreach_weeks:
        warnings.append(
            f"**High weekly TSS** in {', '.join(overreach_weeks)} — "
            "consider whether recovery is adequate."
        )

    if warnings:
        lines += ["## Warnings", ""]
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    # Recommendations
    lines += ["## Recommendations", ""]
    recs = []

    block_merged = _merge_zones(all_results)
    block_low, block_mid, block_high = _zone_band_pcts(block_merged)

    if block_low < 55:
        recs.append(
            f"**Increase Z2 volume**: low-intensity work is at {block_low:.0f}% — "
            "aim for 60–70% to build aerobic base."
        )
    if block_high < 3 and block_avg_IF is not None and block_avg_IF >= 0.80:
        recs.append(
            f"**Add VO2max work**: Z5+ is only {block_high:.1f}% — "
            "include 1 session per week with short intervals at or above VO2max."
        )
    if muddle_count > len(week_labels):
        recs.append(
            "**Polarise training more**: multiple muddle sessions detected. "
            "Commit to either easy (Z1-Z2) or hard (Z4+) sessions — avoid the grey zone."
        )
    if block_avg_IF is not None and block_avg_IF < 0.78 and block_mid < 15:
        recs.append(
            "**Introduce structured threshold work**: overall IF is low and mid-intensity volume "
            "is minimal. A weekly threshold session (e.g. 2×20 min at Z4) would add productive "
            "training stress."
        )

    if not recs:
        recs.append(
            "Training distribution looks solid. Maintain current approach and monitor recovery metrics."
        )

    for r in recs:
        lines.append(f"- {r}")
    lines.append("")

    # PMC Progression
    if weekly_snapshots and len(weekly_snapshots) == len(week_labels):
        lines += ["## Performance Management Chart (PMC)", ""]
        lines += ["| Week | CTL | ATL | TSB | Form |", "|---|---|---|---|---|"]
        for label, snap in zip(week_labels, weekly_snapshots):
            lines.append(
                f"| {label} | {snap.ctl:.1f} | {snap.atl:.1f} | {snap.tsb:+.1f} | {snap.form_label} |"
            )
        lines.append("")
        # CTL trend summary
        ctls = [s.ctl for s in weekly_snapshots]
        if len(ctls) >= 2:
            net = ctls[-1] - ctls[0]
            weeks_span = len(ctls)
            weekly_avg = net / weeks_span
            direction = "building" if net > 0 else "declining"
            lines.append(
                f"CTL {direction}: {net:+.1f} pts over {weeks_span} weeks "
                f"(≈{weekly_avg:+.1f} pts/week avg, safe limit: ≤7 pts/week)."
            )
            lines.append("")

    return "\n".join(lines)
