# New Skills for Better Analysis

## Context

The project currently has two skill/agent files:
- **`cycling-athlete-profile`** — who the athlete is (FTP, zones, goals, physical history)
- **`cycling-coach`** — training methodology (periodization, session types, zone targets, commentary rules)

These cover *training prescription* well but leave gaps in *analysis methodology* — how to interpret and compare metrics across sessions and over time. The code computes power metrics (NP, VI, IF, TSS, zones, peak powers) but lacks longitudinal tracking, HR-based analysis, and deeper interval quality assessment.

After reviewing the full codebase, generated reports, and data available from FIT files, here are **5 recommended skills ranked by impact**. Each one involves both a knowledge skill file (interpretation rules) and code changes (new computations).

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
| 3 | `heart-rate-aerobic-efficiency` | Moderate | Yes | High — historical data proves sensor is actually very reliable (96% uptime in 2025). |
| 4 | `power-duration-profiling` | Moderate | No | Medium-high — PR tracking starts paying off |
| 5 | `session-matching` | Moderate-significant | No (enhanced w/ HR) | Medium — value grows with data volume |

## Recommended Implementation Order

Start with **1 → 2 → 3** (now including HR efficiency since data is reliable). Add **4** alongside or next. Build **5** after 4-6 months of data when workout repetition makes matching meaningful.

## Key Files That Would Be Modified

- `cycling_analyzer/analyzer.py` — new analysis functions (interval fade, EF, CTL/ATL)
- `cycling_analyzer/reporter.py` — new report sections at session/weekly/block levels
- `cycling_analyzer/models.py` — new dataclasses for results
- `report.py` — persistent state management for fitness model and PR records
- `.claude/agents/cycling-coach.md` — update to reference and consume new computed metrics
- New skill files in `.claude/skills/` for each skill
