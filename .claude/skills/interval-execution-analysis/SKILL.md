---
name: interval-execution-analysis
description: Rules for interpreting structured interval execution quality — fade detection, consistency scoring, compliance grading, and HR cost analysis. Use when analyzing structured workouts with defined work intervals (SST, threshold, VO2max).
---

# Interval Execution Analysis

Rules for interpreting structured interval execution quality — fade detection, consistency scoring, compliance grading, and HR cost analysis.

## When to Apply

Use these rules when analyzing structured workouts with defined work intervals (SST, threshold, VO2max). The code automatically identifies work intervals as laps with target power >= 75% FTP and requires at least 2 work intervals for analysis.

## Metric Interpretation

### Coefficient of Variation (CV)

Measures power consistency across work intervals.

| CV | Rating | Interpretation |
|---|---|---|
| < 2% | Excellent | Strong pacing discipline; intervals executed evenly |
| 2–5% | Good | Acceptable variation, especially for longer intervals or outdoor rides |
| > 5% | Inconsistent | Investigate cause — fatigue, motivation loss, or environmental factors |

For indoor trainer sessions, CV should be < 2% in most cases since environmental factors are eliminated. Outdoor rides have more acceptable variation due to terrain and wind.

### Fade Index

Measures power change from first to last work interval. Negative = power dropped.

| Fade | Interpretation |
|---|---|
| ±2% | Negligible — even pacing maintained |
| -2% to -5% | Mild fade — normal for longer threshold efforts (20+ min intervals) |
| < -5% | Significant fade — session may have been too ambitious, or recovery between intervals was insufficient |
| +2% to +5% | Mild positive build — conservative start, good negative split execution |
| > +5% | Strong build — first intervals may have been too easy; consider starting closer to target |

Context matters: mild fade in 4×20 min SST intervals is more acceptable than in 4×5 min threshold intervals. Fade in the final interval only (others stable) suggests the athlete found their limit — this is productive. Progressive fade across all intervals suggests the session intensity was set too high.

### Target Compliance

Percentage of work intervals where average power fell within the prescribed target range.

| Compliance | Interpretation |
|---|---|
| 100% | Perfect execution |
| 75–99% | Good — minor deviations acceptable if systematic (e.g., consistently +5W above target) |
| 50–74% | Marginal — targets may need adjustment or pacing discipline needs work |
| < 50% | Poor — targets are likely misaligned with current fitness; reassess FTP |

Systematic over-target (all intervals above range) suggests FTP may be understated — flag for reassessment. Systematic under-target may indicate fatigue, illness, or FTP regression.

### Cardiac Drift

HR change from first to last work interval at similar power output. Only available when HR data is present.

| Drift | Interpretation |
|---|---|
| < 3% | Stable — effort well within aerobic capacity |
| 3–5% | Normal drift — expected for sustained SST/threshold work |
| > 5% | Significant — approaching aerobic ceiling; consider shorter intervals or lower intensity |
| Negative | Unusual — likely warmup effect (first interval started cold) or decreasing effort |

### Power:HR Ratio (Efficiency)

Tracks how much power is produced per heartbeat across work intervals. Declining ratio = increasing cardiac cost for the same output.

- **Stable or rising**: Good aerobic efficiency; effort is sustainable
- **Declining > 5%**: Fatigue accumulating; HR cost increasing for the same power output
- **Declining > 10%**: Session exceeded sustainable capacity; the athlete is digging into reserves

## Coaching Decision Rules

1. **Fade > 5% across work intervals** → reduce interval count or duration next session, or add 1 min rest between intervals
2. **CV > 5%** → focus on pacing discipline; use ERG mode or tighter power targets
3. **Cardiac drift > 5% combined with fade > 3%** → session exceeded aerobic capacity; reduce intensity by 5–10W next time
4. **All intervals above target** → FTP may be understated; schedule an assessment (MLSS or ramp test)
5. **Compliance < 75%** → targets may be set too high; if consistent across sessions, lower FTP estimate by 3–5%
6. **CV < 1% on trainer** → execution is locked in; consider progressing to next intensity tier
7. **No fade with stable HR** → session was well-calibrated; safe to add 1 interval or 2–5 min duration next time

## Recovery Between Intervals

When interpreting rest laps between work intervals (not currently computed but useful context):
- HR should drop 15–25 bpm during a 5 min recovery interval
- If HR fails to drop > 10 bpm in 5 min, the athlete is accumulating significant fatigue
- Recovery power should be < 60% FTP (true recovery, not tempo recovery)

## Interaction with Other Skills

- **cycling-coach**: Fade and compliance data inform periodization decisions — persistent fade suggests the current training block intensity is too high
- **cycling-athlete-profile**: CV and compliance patterns reveal whether the athlete's current FTP setting is accurate
- **fitness-fatigue-model** (future): High cardiac drift correlates with low TSB (accumulated fatigue)
