---
name: power-duration-profiling
description: Check for FTP staleness, evaluate power-duration phenotype (Sprinter vs. Diesel), and interpret power duration progress across all-time, 1-year, and 30-day windows.
---

# Power Duration Profiling — Interpretation Rules

## Standard Durations and Energy Systems

| Duration | Label | Primary Energy System |
|---|---|---|
| 5 sec | 5 sec | Neuromuscular / peak sprint (ATP-PCr) |
| 10 sec | 10 sec | Neuromuscular / sprint capacity |
| 15 sec | 15 sec | Anaerobic alactic / sprint endurance |
| 30 sec | 30 sec | Anaerobic alactic–lactic transition |
| 1 min | 1 min | Anaerobic capacity / MAP proxy |
| 3 min | 3 min | VO2max territory |
| 5 min | 5 min | VO2max (best 5-min ~ 106–110% of FTP for well-trained) |
| 10 min | 10 min | Threshold / sustained VO2max |
| 20 min | 20 min | Functional Threshold Power (FTP proxy × 0.95) |
| 30 min | 30 min | Near-FTP sustained output |
| 40 min | 40 min | Threshold endurance |
| 60 min | 60 min | True hour power / aerobic ceiling |

## Phenotype Classification

Classification uses three ratios derived from all-time bests. Rules in priority order:

1. **Sprinter**: 5s:5min ratio > 3.5x — dominant neuromuscular capacity relative to aerobic.
2. **TT/Diesel**: 5min:20min ratio < 1.10x — aerobic engine dominates, minimal anaerobic reserve. This athlete: 1.08x — confirmed TT/Diesel.
3. **Pursuiter**: 5min:20min ratio > 1.20x — strong anaerobic capacity extends into 5-min duration.
4. **All-Rounder**: 5min:20min 1.10–1.20x — balanced across systems.

Confidence levels:
- **High**: ≥30 sessions with 5-min data
- **Moderate**: 10–29 sessions
- **Low**: <10 sessions (profile is unreliable, do not over-interpret)

## FTP Staleness Detection

FTP is flagged as stale when **both** conditions hold:
1.  **Implied FTP exceeds current by >5%:** Calculated using the **"Sliding Scale"** methodology for any near-maximal or "to failure" effort between 20 and 60 minutes.
2.  **Consistency:** ≥2 independent sessions show this implied improvement.

### The Sliding Scale Methodology
(Cross-reference: [Athlete Profile Evaluation Methodology](../cycling-athlete-profile/SKILL.md#evaluation-methodology-the-sliding-scale))

For efforts between 20 and 60 minutes, use linear interpolation to derive implied FTP:
- **20 min:** 95.0% of avg power
- **60 min:** 100.0% of avg power
- **Formula:** `implied_FTP = avg_power * (0.95 + (duration_min - 20) * 0.00125)`

*Example:* A 40-minute "to failure" effort at 300W implies an FTP of `300 * (0.95 + (40-20) * 0.00125)` = `300 * 0.975` = **292.5 W**.

**False-positive avoidance**: A single exceptional ride is insufficient — two independent sessions (or one formal test + one field proxy) are required to confirm staleness. This prevents over-reacting to one-off efforts or environmental assists (e.g. strong tailwinds on long segments).

When stale: suggest the new `implied_FTP` based on the most representative "to failure" effort.

## FTP Update Protocol: "The Three-File Rule"

If the user **accepts** an FTP update, you MUST update the following three files in a single turn to ensure system-wide consistency:

1.  **`athlete.json`**: Update the `"ftp"` field (the machine-readable source of truth).
2.  **`cycling-athlete-profile/FTP_HISTORY.md`**: Append a new entry to the chronological log.
3.  **`cycling-athlete-profile/SKILL.md`**: Update the "Key Numbers" and recalculate all Coggan Power Zones.

Do NOT update one without the others.

## Progress Tracking Interpretation

| Delta | Interpretation |
|---|---|
| > +5% | Meaningful improvement — confirm with follow-up session |
| +1%–+5% | Real improvement, especially if recorded in ≥2 sessions |
| ±1% | Within measurement noise — monitor trend |
| -1%–-5% | Likely fatigue — check TSB, recent training load |
| < -5% | Significant decline — investigate recovery or health |

Prefer comparing period bests (e.g. current 4-week block vs. previous) over single-session PRs for trend analysis. Single-session PRs are motivating but can reflect pacing, conditions, or freshness rather than fitness change.

## Seasonal Expectations

- **Base phase** (Z1-Z2 focus): 20-min and 60-min bests improve gradually; 5-sec may decline as sprint sessions are de-emphasised.
- **Build phase** (SST/threshold): 5-min and 20-min bests improve most; 1-min anaerobic capacity often plateaus.
- **Peak phase**: All durations should be near or at season bests; PRs at 5-min and 20-min are the target outcome.
- **Off-season/deload**: Expected 5–10% decline across all durations; do not flag these as concerning.

## PR Extraction Script

`pr_report.py` in the project root extracts power PRs from `data/power_records.json`. Run with:

```bash
uv run pr_report.py
```

Outputs:
1. A compact **summary table** — all durations × time windows (30d, 90d, 1yr, all-time) showing watts and W/kg side-by-side
2. **Detailed sections** per window with watts, W/kg, and the date each PR was set

Source data: `data/power_records.json` (keyed by duration in seconds → timestamp → watts). Weight pulled from `athlete.json`.

## W/kg Limitations

All W/kg values in `power_records.json` are computed using the **current static weight** from `athlete.json`. Historical weight data is not recorded, so W/kg for past efforts may be inaccurate if body weight has changed significantly. Do not draw precise conclusions from W/kg trends over long time horizons (e.g. year or all-time windows). Watts absolute values are the reliable comparison unit across time.

## Interaction with Other Skills

- **fitness-fatigue-model**: Low TSB (< -10) suppresses peak power expression. A "non-PR" session during a block of fatigue (TSB < -15) is not evidence of fitness loss. Always check TSB context before interpreting power duration results.
- **interval-execution-analysis**: Interval execution quality affects whether the power curve reflects true capacity. Faded intervals underrepresent 5-min and 20-min potential. A session with poor execution (fade > 5%) should not be used as a reference for FTP staleness assessment.
- **heart-rate-aerobic-efficiency**: Rising EF (efficiency factor) over time with stable or improving 20-min power is strong evidence of real fitness improvement, even if 20-min peak watts haven't set a PR yet.
