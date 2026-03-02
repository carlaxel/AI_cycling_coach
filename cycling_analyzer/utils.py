"""Shared formatting utilities for cycling_analyzer."""


def fmt_duration(seconds: float | None, show_seconds: bool = True) -> str:
    """Format seconds to human-readable duration string.

    show_seconds=True (default): '1h 02m 30s'
    show_seconds=False: '1h 02m'
    """
    if seconds is None:
        return "—"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        base = f"{h}h {m:02d}m"
        return f"{base} {sec:02d}s" if show_seconds else base
    if show_seconds:
        return f"{m}m {sec:02d}s"
    return f"{m}m"


def fmt_dist(meters: float | None) -> str:
    if meters is None:
        return "—"
    return f"{meters / 1000:.2f} km"


def fmt_speed(mps: float | None) -> str:
    if mps is None:
        return "—"
    return f"{mps * 3.6:.1f} km/h"


def bar(pct: float, width: int = 20) -> str:
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)
