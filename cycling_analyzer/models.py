from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RecordPoint:
    timestamp: Optional[datetime] = None
    power: Optional[int] = None
    heart_rate: Optional[int] = None
    cadence: Optional[int] = None
    speed: Optional[float] = None
    altitude: Optional[float] = None
    distance: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    # Pedaling dynamics (Favero Assioma and compatible pedals)
    left_pct: Optional[float] = None                    # decoded left power %
    left_torque_effectiveness: Optional[float] = None
    right_torque_effectiveness: Optional[float] = None
    left_pedal_smoothness: Optional[float] = None
    right_pedal_smoothness: Optional[float] = None
    temperature: Optional[float] = None


@dataclass
class LapSummary:
    lap_number: int = 0
    start_time: Optional[datetime] = None
    elapsed_time: Optional[float] = None
    timer_time: Optional[float] = None
    distance: Optional[float] = None
    avg_power: Optional[float] = None
    max_power: Optional[int] = None
    avg_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    avg_cadence: Optional[int] = None
    ascent: Optional[float] = None
    normalized_power: Optional[float] = None
    total_work_kj: Optional[float] = None
    total_calories: Optional[int] = None
    avg_temperature: Optional[float] = None
    target_power_low: Optional[int] = None   # from embedded workout step
    target_power_high: Optional[int] = None


@dataclass
class HRZoneDistribution:
    z1_time_seconds: int = 0
    z2_time_seconds: int = 0
    z3_time_seconds: int = 0
    z4_time_seconds: int = 0
    z5_time_seconds: int = 0
    z6_time_seconds: int = 0


@dataclass
class SessionSummary:
    start_time: Optional[datetime] = None
    elapsed_time: Optional[float] = None
    timer_time: Optional[float] = None
    distance: Optional[float] = None
    avg_power: Optional[float] = None
    max_power: Optional[int] = None
    avg_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    calories: Optional[int] = None
    ascent: Optional[float] = None
    sport: Optional[str] = None
    sub_sport: Optional[str] = None
    total_work_kj: Optional[float] = None
    avg_temperature: Optional[float] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    efficiency_factor: Optional[float] = None
    aerobic_decoupling_pct: Optional[float] = None
    hr_zones: Optional[HRZoneDistribution] = None


@dataclass
class WorkoutData:
    session: SessionSummary
    laps: list[LapSummary] = field(default_factory=list)
    records: list[RecordPoint] = field(default_factory=list)
