import math
import warnings
from pathlib import Path

import fitdecode

from .models import LapSummary, RecordPoint, SessionSummary, WorkoutData

_SEMICIRCLES_TO_DEG = 180.0 / (2**31)


def _get(frame: fitdecode.FitDataMessage, field_name: str, default=None):
    if frame.has_field(field_name):
        val = frame.get_value(field_name)
        return val if val is not None else default
    return default


def _decode_left_pct(raw: int | None) -> float | None:
    """Decode Garmin left_right_balance uint8 to left-side percentage.

    Bit 7 set means the value encodes the right-side percentage; bits 0-6
    are the percentage for that side.
    """
    if raw is None:
        return None
    
    if isinstance(raw, str):
        try:
            raw = int(raw)
        except (ValueError, TypeError):
            return None

    if raw > 128:
        return float(100 - (raw - 128))
    return float(raw)


def _decode_power_target(raw: int | None) -> int | None:
    """Decode FIT workout step custom power target to watts.

    Values > 1000 encode watts as (value - 1000); values ≤ 1000 are
    percent-of-FTP targets which we don't resolve here.
    """
    if raw is None or raw <= 1000:
        return None
    return raw - 1000


def parse_fit_file(path: str | Path) -> WorkoutData:
    records: list[RecordPoint] = []
    laps: list[LapSummary] = []
    session: SessionSummary | None = None
    lap_count = 0
    workout_steps: list[dict] = []  # accumulated before laps are emitted

    with fitdecode.FitReader(str(path)) as fit:
        for frame in fit:
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue

            if frame.name == "workout_step":
                workout_steps.append({
                    "target_low": _decode_power_target(_get(frame, "custom_target_power_low")),
                    "target_high": _decode_power_target(_get(frame, "custom_target_power_high")),
                })

            elif frame.name == "record":
                lr_raw = _get(frame, "left_right_balance")
                lat_raw = _get(frame, "position_lat")
                lon_raw = _get(frame, "position_long")
                records.append(
                    RecordPoint(
                        timestamp=_get(frame, "timestamp"),
                        power=_get(frame, "power"),
                        heart_rate=_get(frame, "heart_rate"),
                        cadence=_get(frame, "cadence"),
                        speed=_get(frame, "speed"),
                        altitude=_get(frame, "altitude"),
                        distance=_get(frame, "distance"),
                        lat=lat_raw * _SEMICIRCLES_TO_DEG if lat_raw is not None else None,
                        lon=lon_raw * _SEMICIRCLES_TO_DEG if lon_raw is not None else None,
                        left_pct=_decode_left_pct(lr_raw),
                        left_torque_effectiveness=_get(frame, "left_torque_effectiveness"),
                        right_torque_effectiveness=_get(frame, "right_torque_effectiveness"),
                        left_pedal_smoothness=_get(frame, "left_pedal_smoothness"),
                        right_pedal_smoothness=_get(frame, "right_pedal_smoothness"),
                        temperature=_get(frame, "temperature"),
                    )
                )

            elif frame.name == "lap":
                step = workout_steps[lap_count] if lap_count < len(workout_steps) else {}
                work_j = _get(frame, "total_work")
                laps.append(
                    LapSummary(
                        lap_number=lap_count,
                        start_time=_get(frame, "start_time"),
                        elapsed_time=_get(frame, "total_elapsed_time"),
                        timer_time=_get(frame, "total_timer_time"),
                        distance=_get(frame, "total_distance"),
                        avg_power=_get(frame, "avg_power"),
                        max_power=_get(frame, "max_power"),
                        avg_heart_rate=_get(frame, "avg_heart_rate"),
                        max_heart_rate=_get(frame, "max_heart_rate"),
                        avg_cadence=_get(frame, "avg_cadence"),
                        ascent=_get(frame, "total_ascent"),
                        normalized_power=_get(frame, "normalized_power"),
                        total_work_kj=work_j / 1000 if work_j is not None else None,
                        total_calories=_get(frame, "total_calories"),
                        avg_temperature=_get(frame, "avg_temperature"),
                        target_power_low=step.get("target_low"),
                        target_power_high=step.get("target_high"),
                    )
                )
                lap_count += 1

            elif frame.name == "session":
                sport_raw = _get(frame, "sport")
                sub_sport_raw = _get(frame, "sub_sport")
                work_j = _get(frame, "total_work")
                session = SessionSummary(
                    start_time=_get(frame, "start_time"),
                    elapsed_time=_get(frame, "total_elapsed_time"),
                    timer_time=_get(frame, "total_timer_time"),
                    distance=_get(frame, "total_distance"),
                    avg_power=_get(frame, "avg_power"),
                    max_power=_get(frame, "max_power"),
                    avg_heart_rate=_get(frame, "avg_heart_rate"),
                    max_heart_rate=_get(frame, "max_heart_rate"),
                    calories=_get(frame, "total_calories"),
                    ascent=_get(frame, "total_ascent"),
                    sport=str(sport_raw) if sport_raw is not None else None,
                    sub_sport=str(sub_sport_raw) if sub_sport_raw is not None else None,
                    total_work_kj=work_j / 1000 if work_j is not None else None,
                    avg_temperature=_get(frame, "avg_temperature"),
                    min_temperature=_get(frame, "min_temperature"),
                    max_temperature=_get(frame, "max_temperature"),
                )

    if session is None:
        raise ValueError(f"No session message found in {path}")

    if workout_steps and laps and len(workout_steps) != len(laps):
        warnings.warn(
            f"{Path(path).name}: workout step count ({len(workout_steps)}) does not match "
            f"lap count ({len(laps)}) — target power may be misaligned",
            stacklevel=2,
        )

    return WorkoutData(session=session, laps=laps, records=records)
