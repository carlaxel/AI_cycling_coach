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

    def to_dict(self):
        return {
            "z1_time_seconds": self.z1_time_seconds,
            "z2_time_seconds": self.z2_time_seconds,
            "z3_time_seconds": self.z3_time_seconds,
            "z4_time_seconds": self.z4_time_seconds,
            "z5_time_seconds": self.z5_time_seconds,
            "z6_time_seconds": self.z6_time_seconds,
        }


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


@dataclass
class PeakPowerEntry:
    label: str
    watts: int
    pct_ftp: Optional[float] = None
    w_kg: Optional[float] = None
    is_pr: bool = False
    improvement_watts: Optional[int] = None
    previous_best: Optional[int] = None

    def to_dict(self):
        return {
            "label": self.label,
            "watts": self.watts,
            "pct_ftp": self.pct_ftp,
            "w_kg": self.w_kg,
            "is_pr": self.is_pr,
            "improvement_watts": self.improvement_watts,
            "previous_best": self.previous_best,
        }


@dataclass
class SessionReportEnrichment:
    athlete_comment: Optional[str] = None

    def to_dict(self):
        return {
            "athlete_comment": self.athlete_comment,
        }


@dataclass
class SessionReportData:
    version: str = "1.0"
    metadata: dict = field(default_factory=dict)
    historical_context: dict = field(default_factory=dict)
    stats: dict = field(default_factory=dict)
    power: dict = field(default_factory=dict)
    hr: dict = field(default_factory=dict)
    pedaling: dict = field(default_factory=dict)
    peaks: list[PeakPowerEntry] = field(default_factory=list)
    laps: list[dict] = field(default_factory=list)
    interval_analysis: Optional[dict] = None
    zones: list[dict] = field(default_factory=list)
    commentary: dict = field(default_factory=dict)
    enrichment: SessionReportEnrichment = field(default_factory=SessionReportEnrichment)

    def to_dict(self):
        return {
            "version": self.version,
            "metadata": self.metadata,
            "historical_context": self.historical_context,
            "stats": self.stats,
            "power": self.power,
            "hr": self.hr,
            "pedaling": self.pedaling,
            "peaks": [p.to_dict() for p in self.peaks],
            "laps": self.laps,
            "interval_analysis": self.interval_analysis,
            "zones": self.zones,
            "commentary": self.commentary,
            "enrichment": self.enrichment.to_dict(),
        }


@dataclass
class CommentaryBlock:
    title: str
    content: str

    def to_dict(self):
        return {
            "title": self.title,
            "content": self.content,
        }


@dataclass
class WeeklyReportData:
    version: str = "1.0"
    week_id: str = ""
    period: str = ""
    ftp: Optional[int] = None
    weight: Optional[float] = None
    summary: dict = field(default_factory=dict)
    fitness: dict = field(default_factory=dict)
    peaks: list[dict] = field(default_factory=list)
    sessions: list[dict] = field(default_factory=list)
    zones: list[dict] = field(default_factory=list)
    hr_zones: Optional[dict] = None
    model_alignment: dict = field(default_factory=dict)
    commentary: list[CommentaryBlock] = field(default_factory=list)

    def to_dict(self):
        return {
            "version": self.version,
            "week_id": self.week_id,
            "period": self.period,
            "ftp": self.ftp,
            "weight": self.weight,
            "summary": self.summary,
            "fitness": self.fitness,
            "peaks": self.peaks,
            "sessions": self.sessions,
            "zones": self.zones,
            "hr_zones": self.hr_zones,
            "model_alignment": self.model_alignment,
            "commentary": [c.to_dict() for c in self.commentary],
        }


@dataclass
class BlockReportData:
    version: str = "1.0"
    block_id: str = ""
    period: str = ""
    weeks: list[str] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    fitness_trend: list[dict] = field(default_factory=list)
    peaks: list[dict] = field(default_factory=list)
    weekly_summaries: list[dict] = field(default_factory=list)
    zones: list[dict] = field(default_factory=list)
    commentary: list[CommentaryBlock] = field(default_factory=list)

    def to_dict(self):
        return {
            "version": self.version,
            "block_id": self.block_id,
            "period": self.period,
            "weeks": self.weeks,
            "summary": self.summary,
            "fitness_trend": self.fitness_trend,
            "peaks": self.peaks,
            "weekly_summaries": self.weekly_summaries,
            "zones": self.zones,
            "commentary": [c.to_dict() for c in self.commentary],
        }
