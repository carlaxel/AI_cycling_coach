---
name: fitness-fatigue-model
description: Rules for interpreting the Performance Management Chart (PMC) — CTL, ATL, TSB computation, ramp rate thresholds, form assessment, and recovery recommendations. Use when reasoning about training load, fatigue state, or periodization decisions.
---

# Fitness-Fatigue Model (PMC)

Rules for interpreting the Performance Management Chart — CTL, ATL, TSB computation, ramp rate thresholds, form assessment, and recovery recommendations.

## Definitions

**CTL — Chronic Training Load (Fitness)**
42-day exponential moving average of daily TSS. Represents accumulated aerobic fitness. Grows slowly over weeks and months. A single session cannot significantly change CTL.

**ATL — Acute Training Load (Fatigue)**
7-day exponential moving average of daily TSS. Represents recent accumulated fatigue. Responds quickly: a hard week spikes ATL within days; a rest day brings it down fast.

**TSB — Training Stress Balance (Form)**
TSB = CTL − ATL. Positive means fresher than the chronic baseline (rested). Negative means more fatigued than the baseline (deep in a training block).

---

## Form Labels (TSB Interpretation)

| TSB Range | Label | Interpretation |
|---|---|---|
| > +10 | Fresh | Significantly rested; ready to race or peak. Sustained values here = undertrained or in taper. |
| 0 to +10 | Neutral+ | Slightly fresh; ideal for key sessions and races. |
| −10 to 0 | Neutral− | Mild fatigue; normal training state. Hard sessions remain productive. |
| −20 to −10 | Fatigued | Moderate fatigue. Typical for a mid-block week with 3+ quality sessions. Performance is slightly suppressed. |
| −30 to −20 | Very Fatigued | Deep training load. Recovery sessions should be prioritized. Race performance will suffer. |
| < −30 | Overreached | Excessive cumulative load. Risk of injury, illness, and stagnation. Recovery week required immediately. |

---

## Ramp Rate (CTL Weekly Change)

This athlete's safe ramp rate is **3–7 CTL points per week** (conservative, appropriate for base-building phase at 95 kg). Note: Standard coaching guidelines (Friel) often suggest a max of 5-8 points per week, so 3-7 per week is a solid conservative target without being too stagnant.

| Weekly Ramp | Status | Action |
|---|---|---|
| ≤ 3 pts | OK | Sustainable progression or recovery phase. |
| 4–7 pts | Elevated | Within limit but approaching ceiling — monitor closely. |
| > 7 pts | Excessive | High injury/illness risk. Reduce next week's load or insert a recovery week. |
| Negative | Decreasing | CTL is falling. Intentional (deload/taper) or unintentional (missed training). Investigate cause. |

---

## CTL Target Ranges

| CTL | Interpretation for this athlete |
|---|---|
| < 30 | Very low base; aerobic capacity limited. Only appropriate post-layoff. |
| 30–50 | Moderate base; capable of consistent 6–8h weeks. Current starting range. |
| 50–70 | Good base; sustained threshold work and long Z2 rides feel manageable. Target for this season. |
| 70–85 | Strong base; competitive amateur range. Secondary season target. |
| > 85 | Elite amateur/gran fondo racer territory. Long-term multi-year goal. |

---

## ATL Interpretation

ATL reflects how fatigued the athlete is from recent training. Context matters:

- **ATL spike after a hard week** (e.g., Thailand block): expected. TSB will be deeply negative. Require 5–10 days of reduced load before TSB recovers above −10.
- **ATL chronically elevated** (> 1.5× CTL for 2+ weeks): signals insufficient recovery. Overreaching risk — reduce volume.
- **ATL near zero**: athlete is not training enough to stimulate adaptation.

---

## Recovery Window Estimates

After a hard week (TSS > 500), estimate recovery timeline:

| TSB at end of hard week | Days to TSB > −10 at rest |
|---|---|
| −30 | ~5 days |
| −40 | ~8 days |
| −50 | ~11 days |

These are approximations. HR data (elevated HR at known power), motivation, and sleep quality refine the estimate. The code does not yet have HR trending; use subjective feel as the secondary signal.

---

## Seasonal Planning Context

**Base phase (current):** CTL should be steadily rising at ≤ 8 pts/month. TSB should be moderately negative (−10 to −20) on hard weeks, rebounding to neutral (+/− 5) during rest days within the week.

**Build phase (future):** Higher average IF sessions (SST → threshold → VO2max). CTL growth may slow as intensity increases. TSB management becomes critical — target TSB of 0 to +10 before key threshold tests.

**Peak/Race phase:** Taper 10–14 days out. CTL drops slightly; ATL falls faster. TSB rises to +15 to +25. Do not let TSB exceed +30 (too much freshness = lost fitness).

---

## Data Accuracy Notes

CTL values are underestimated when fewer than 42 days of history are available (the EMA needs time to "fill up"). With 9 weeks of data, CTL values from weeks 1–4 will be lower than reality. Values stabilise around week 6+. Run `report.py block` to bootstrap the full history from all processed sessions before using CTL for planning.

Sessions without recorded TSS (e.g. incomplete FIT files) will appear as zero-TSS days, artificially depressing CTL. Flag these sessions and estimate TSS manually if needed.
