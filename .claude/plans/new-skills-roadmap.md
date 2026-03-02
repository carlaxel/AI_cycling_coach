# New Skills for Better Analysis

## Context

The project currently has two skill/agent files:
- **`cycling-athlete-profile`** — who the athlete is (FTP, zones, goals, physical history)
- **`cycling-coach`** — training methodology (periodization, session types, zone targets, commentary rules)

These cover *training prescription* well but leave gaps in *analysis methodology* — how to interpret and compare metrics across sessions and over time. The code computes power metrics (NP, VI, IF, TSS, zones, peak powers) but lacks longitudinal tracking, HR-based analysis, and deeper interval quality assessment.

After reviewing the full codebase, generated reports, and data available from FIT files, here are **5 recommended skills ranked by impact**. Each one involves both a knowledge skill file (interpretation rules) and code changes (new computations).

---

## Rank 2: `fitness-fatigue-model`

**What:** Rules for interpreting the Performance Management Chart (PMC) — CTL, ATL, TSB computation, ramp rate thresholds, form/freshness assessment.

**Why this athlete:** The coach agent already references CTL/ATL/TSB numbers ("Sustainable CTL: 55-80", "Ramp rate: no more than 5-8 points/month") but the code computes none of them. With 9 weeks of data (~40 sessions), CTL values are now meaningful. The Thailand week (W05, 937 TSS) followed by a single-session W07 is a textbook overreach-recovery pattern that the code cannot detect.

**Unlocks:**
- Daily CTL (42-day EMA), ATL (7-day EMA), TSB (CTL - ATL)
- Ramp rate tracking with warnings when exceeding safe limits
- Recovery week recommendations when TSB drops below -20/-30
- Form predictions ("current TSB is -15, expect reduced capacity")
- Block analysis: CTL trend line, overreach/absorption period identification

**Code changes:** Significant — needs a persistent state file (daily TSS history as JSON/CSV) since CTL spans across weekly `report.py` invocations. New module (e.g., `fitness_model.py`).

**Dependencies:** Requires historical TSS data. 9 weeks is enough to seed the model. No HR dependency.

---

## Rank 3: `power-duration-profiling`

**What:** Rules for interpreting power-duration curves — PR tracking, phenotype classification, progress comparison, FTP validation from the curve.

**Why this athlete:** Current reports show peak powers at 6 fixed durations per session but never compare across sessions. The Jan 15 session had a 20-min peak of 294W — nearly equal to the stated 295W FTP. Tracking whether that number creeps up week over week is the most direct indicator that training is working. The flat 5min-to-20min curve (only 5W drop) reveals a strong steady-state profile aligned with TT goals, but this is never surfaced.

**Unlocks:**
- All-time and rolling best-power records per duration
- PR flags in session reports ("new 20-min best: 298W, previous: 294W")
- Power profile classification (sprinter vs TT vs climber phenotype from ratios)
- FTP staleness detection (when 20-min best regularly exceeds FTP × 1.05)
- Progress tracking: compare current peaks to a reference period

**Code changes:** Moderate — persistent records store (JSON), extend existing `_peak_powers` function to check against stored records. New report sections.

**Dependencies:** None. Power data always available. Value compounds over time.

---

## Rank 4: `heart-rate-aerobic-efficiency`

**What:** Rules for HR zone analysis, aerobic decoupling (power:HR drift in steady-state efforts), Efficiency Factor (NP/avg HR), and cardiac drift detection.

**Why this athlete:** Aerobic decoupling directly predicts whether the athlete can hold power for 60+ minutes — the core goal. The manually-written January monthly report already demonstrates the value ("150 bpm at IF 0.683 is 10-15 bpm above baseline"), but the code doesn't compute any of this. EF trending would show aerobic fitness improvements over weeks.

**Unlocks:**
- HR zone distribution (5-zone model from estimated LTHR ~170 bpm)
- Aerobic decoupling: split steady-state efforts in half, compare NP:HR (>5% drift = aerobic ceiling reached)
- Efficiency Factor (NP/avgHR) trending across weeks
- Illness/fatigue detection from elevated HR at known power outputs

**Code changes:** Moderate — new analysis functions for EF, decoupling (requires identifying sustained steady-state segments). Conditional report sections.

**Dependencies:** **Requires HR data.** Currently intermittent (present W01-W05, absent W08-W09). High-value when sensor is connected, useless when not. Ranked 4th due to this gap — moves to rank 2 once HR is consistently available.

---

## Rank 5: `session-matching`

**What:** Rules for comparing repeated workout formats — fingerprinting workouts, tracking improvements in specific interval formats, detecting FTP staleness from repeated session data.

**Why this athlete:** Several workout formats repeat across weeks (Z2 at ~200W, SST with 10-min work intervals). Comparing the same workout across dates reveals whether training is producing adaptation, but this currently requires manually reading multiple session files.

**Unlocks:**
- Automatic workout fingerprinting (lap count, duration pattern, target power ranges)
- Side-by-side comparison tables for matched sessions
- Progress metrics: same workout, different date — higher power? Lower HR? Less fade?
- FTP staleness detection from consistent target overshoot

**Code changes:** Moderate-to-significant — fingerprinting algorithm, persistent session index, new comparison report type.

**Dependencies:** Needs accumulated history. 9 weeks is a starting point; value compounds over months.

---

## Summary

| Rank | Skill | Code Effort | HR Needed? | Impact Now |
|------|-------|-------------|-----------|------------|
| 1 | `interval-execution-analysis` | Moderate | No (enhanced w/ HR) | High — every SST/threshold session |
| 2 | `fitness-fatigue-model` | Significant | No | High — CTL/ATL immediately computable |
| 3 | `power-duration-profiling` | Moderate | No | Medium-high — PR tracking starts paying off |
| 4 | `heart-rate-aerobic-efficiency` | Moderate | Yes | Medium — blocked by sensor intermittency |
| 5 | `session-matching` | Moderate-significant | No (enhanced w/ HR) | Medium — value grows with data volume |

## Recommended Implementation Order

Start with **1 → 2 → 3** (all power-only, immediately useful). Add **4** once HR sensor is reconnected. Build **5** after 4-6 months of data when workout repetition makes matching meaningful.

## Key Files That Would Be Modified

- `cycling_analyzer/analyzer.py` — new analysis functions (interval fade, EF, CTL/ATL)
- `cycling_analyzer/reporter.py` — new report sections at session/weekly/block levels
- `cycling_analyzer/models.py` — new dataclasses for results
- `report.py` — persistent state management for fitness model and PR records
- `.claude/agents/cycling-coach.md` — update to reference and consume new computed metrics
- New skill files in `.claude/skills/` for each skill
