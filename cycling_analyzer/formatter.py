import dataclasses
import json
from datetime import datetime
from typing import Any

from .analyzer import AnalysisResult
from .utils import fmt_duration, fmt_dist, fmt_speed, bar


def format_text(result: AnalysisResult) -> str:
    s = result.workout.session
    lines = []

    lines.append("=" * 60)
    lines.append("  CYCLING WORKOUT ANALYSIS")
    lines.append("=" * 60)

    # Session info
    lines.append("\n── SESSION ─────────────────────────────────────────────")
    if s.sport:
        lines.append(f"  Sport        : {s.sport}")
    if s.start_time:
        lines.append(f"  Date         : {s.start_time.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"  Duration     : {fmt_duration(s.timer_time or s.elapsed_time)}")
    lines.append(f"  Distance     : {fmt_dist(s.distance)}")
    if s.calories:
        lines.append(f"  Calories     : {s.calories} kcal")
    if s.ascent:
        lines.append(f"  Ascent       : {s.ascent:.0f} m")

    # Power
    lines.append("\n── POWER ───────────────────────────────────────────────")
    lines.append(f"  Avg Power    : {s.avg_power:.0f} W" if s.avg_power else "  Avg Power    : —")
    lines.append(f"  Max Power    : {s.max_power} W" if s.max_power else "  Max Power    : —")
    if result.normalized_power:
        lines.append(f"  Norm. Power  : {result.normalized_power:.0f} W")
    if result.variability_index:
        lines.append(f"  Variab. Index: {result.variability_index:.3f}")
    if result.ftp:
        lines.append(f"  FTP          : {result.ftp} W")
    if result.intensity_factor:
        lines.append(f"  IF           : {result.intensity_factor:.3f}")
    if result.tss:
        lines.append(f"  TSS          : {result.tss:.1f}")
    if result.weight and result.weight > 0:
        if s.avg_power:
            lines.append(f"  Avg W/kg     : {s.avg_power / result.weight:.2f} W/kg")
        if result.normalized_power:
            lines.append(f"  NP W/kg      : {result.normalized_power / result.weight:.2f} W/kg")

    # Heart Rate
    lines.append("\n── HEART RATE ──────────────────────────────────────────")
    lines.append(f"  Avg HR       : {s.avg_heart_rate} bpm" if s.avg_heart_rate else "  Avg HR       : —")
    lines.append(f"  Max HR       : {s.max_heart_rate} bpm" if s.max_heart_rate else "  Max HR       : —")

    # Cadence / Speed
    lines.append("\n── OTHER ───────────────────────────────────────────────")
    records = result.workout.records
    cad_values = [r.cadence for r in records if r.cadence is not None and r.cadence > 0]
    spd_values = [r.speed for r in records if r.speed is not None]
    if cad_values:
        lines.append(f"  Avg Cadence  : {sum(cad_values) / len(cad_values):.0f} rpm")
        lines.append(f"  Max Cadence  : {max(cad_values)} rpm")
    if spd_values:
        lines.append(f"  Avg Speed    : {fmt_speed(sum(spd_values) / len(spd_values))}")
        lines.append(f"  Max Speed    : {fmt_speed(max(spd_values))}")

    # Laps
    laps = result.workout.laps
    if laps:
        lines.append("\n── LAPS ────────────────────────────────────────────────")
        lines.append(f"  {'Lap':>3}  {'Time':>8}  {'Dist':>8}  {'Avg W':>6}  {'Avg HR':>6}")
        lines.append(f"  {'───':>3}  {'────':>8}  {'────':>8}  {'─────':>6}  {'──────':>6}")
        for lap in laps:
            t = fmt_duration(lap.elapsed_time)
            d = fmt_dist(lap.distance)
            pw = f"{lap.avg_power:.0f}" if lap.avg_power else "—"
            hr = str(lap.avg_heart_rate) if lap.avg_heart_rate else "—"
            lines.append(f"  {lap.lap_number + 1:>3}  {t:>8}  {d:>8}  {pw:>6}  {hr:>6}")

    # Zone distribution
    if result.zones:
        lines.append("\n── POWER ZONES (Coggan) ────────────────────────────────")
        for z in result.zones:
            b = bar(z.percent_of_ride, width=30)
            hi = f"{z.upper_pct * result.ftp:.0f}" if z.upper_pct != float("inf") else "∞"
            lo = f"{z.lower_pct * result.ftp:.0f}"
            lines.append(f"  {z.zone_name:<22} {b} {z.percent_of_ride:5.1f}%  ({z.seconds}s)")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def _default_serializer(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, float) and obj == float("inf"):
        return None
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def format_json(result: AnalysisResult) -> str:
    data = dataclasses.asdict(result)
    return json.dumps(data, indent=2, default=_default_serializer)
