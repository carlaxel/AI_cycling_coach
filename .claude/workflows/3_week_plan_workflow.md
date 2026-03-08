# 3-Week Workout Plan Generation Workflow

This workflow defines the standard operating procedure for generating a 3-week cycling training block for the athlete, ensuring adherence to their profile, schedule, and formatting requirements. It strictly enforces progression toward annual goals and requires adaptation based on the execution of previous blocks.

## 1. Pre-Flight Checks & Retrospective Analysis

Before designing a new block, the AI must evaluate the athlete's current state and historical execution to ensure the new plan is appropriate and safe.

### A. Macro-Cycle Alignment (Yearly Goal)
Activate the `cycling-athlete-profile` and `fitness-fatigue-model` skills to determine where this block fits in the season:
- **Current Phase & Next Phase:** Verify the sequence (e.g., Base Building [SST] -> Threshold Build -> VO2max). Do not skip steps.
- **Current CTL & Target Ramp:** What is the current CTL? Calculate the required weekly ramp rate (target 3–7 CTL points/week) to hit the phase goal (e.g., Q1 target: 58-63 CTL).
- **Current FTP:** Verify the current working FTP (e.g., 290 W).

### B. Multi-Block Retrospective & Trend Analysis
Activate the `session-matching`, `interval-execution-analysis`, `fitness-fatigue-model`, and `heart-rate-aerobic-efficiency` skills to audit the prior **two blocks** (6-8 weeks). **You MUST read the 2 most recent Block Reports (e.g., `reports/YYYY/block_reports/block_*.md` or similar) and the relevant Weekly Summaries (found in `weekly_report.json` and `weekly_summary.md`) to inform this analysis:**
- **Fatigue Check:** Check current TSB and ATL. If TSB is deeply negative (< -20) or ATL is chronically elevated, starting volume must be adjusted.
- **Phenotype & Adaptation Trend:** Evaluate Aerobic Decoupling (Pw:HR) and Fade Index trends across the last TWO blocks. Are they improving or degrading? Do not build a new progression on a short-term anomaly or a false peak. Ensure improvements are sustained over the macro-cycle.
- **Execution Quality:** Evaluate primary interval sessions based on the weekly summaries and coach logs.
  - Was Target Compliance > 75%?
  - Was the Fade Index > 5%?
- **Coach's Notes & Strategy:** Review the "Weekly Critique" (stored as `CommentaryBlock` objects in `weekly_report.json`) and "Qualitative Analysis" (found in `coach_log.json`) for the relevant weeks, and the strategy for the next mesocycle dictated by the block reports.
- **Adaptive Adjustment:** If the athlete struggled (high fade, low compliance, high cardiac drift) in the previous block's progression (e.g., 3x15m SST), the new block **must not** progress to harder intervals (e.g., 2x30m SST) until the previous target is consolidated.

### C. Plan vs. Actual Data Integrity Audit
Before designing the progression, compare the prescribed `%FTP` targets and Work/Recovery durations in the previous block's plan against the actual Normalized Power and time-in-zone achieved (as summarized in the session and weekly reports).
- **Integrity Check:** If the variance between prescribed intensity vs. actual execution is consistently > 5% (over- or under-performing), or if target power was routinely missed, the baseline FTP or weight data **must be re-evaluated** before the next block is planned. This prevents compounding errors in TSS and load planning based on inaccurate baseline data.

## 2. Weekly Schedule Template
Follow the athlete's work/life schedule constraints. Ask to verify any changes before generating the plan. Adjust intensity and volume based on the current phase, target progression, and the retrospective analysis.
- **Monday (WFH):** Structured Intensity (e.g., SST / Threshold).
- **Tuesday (Office):** Rest or Active Recovery (< 55% FTP).
- **Wednesday (WFH):** Structured Intensity (e.g., SST / Threshold).
- **Thursday (Office):** Rest or Active Recovery (< 55% FTP).
- **Friday (WFH):** Structured Intensity or Long Endurance.
- **Saturday:** Long Endurance (Z2: 56–75% FTP).
- **Sunday:** Recovery / Easy Z2 (Always easy post-date night).

## 3. Session Formatting Requirements
Activate the `session-creation` skill and strictly follow its formatting rules for every generated session:
1. **Warm-up:** 
   - Endurance: Max 5 min.
   - Structured: 5 min @ 52% FTP + 10 min @ 63% FTP.
2. **Main Set:** Progress the time-in-zone across the build weeks. Use `%` of FTP for all power targets (e.g., `90%`, not `Z4`).
3. **No Cool-down:** Do not include a planned cool-down block in the structure.
4. **intervals.icu Block:** Include the copy-paste ready text block for direct import.
5. **Nutrition:** Append the post-ride carbohydrate calculation based on ride duration and expected TSS.

## 4. Execution Steps

When asked to generate a 3-week plan, the AI should execute the following sequence:

### Step 1: Design the Progression
**Delegate this step to the `cycling-coach` subagent.** 
- Provide the subagent with the findings from the **Pre-Flight Checks**, **Multi-Block Retrospective**, and **Plan vs. Actual Data Integrity Audit**.
- The subagent must define the primary progression target for the block (e.g., consolidating 3x15m SST before moving to 2x20m SST).
- Ensure the week after the 3rd week is a clear recovery week (volume reduced by 30-40%, keeping one intensity session). This directly addresses the 2025 lesson of missing systematic recovery weeks.

### Step 2: Draft the Block Plan
Create a high-level overview document using the standard format (e.g., `workout_plans/YYYY_monthXX-XX.md`) detailing the daily volume, target TSS, and session goals across the 21 days.

### Step 3: Generate the intervals.icu Blocks
Embed the workout text blocks directly into the plan document for every structured session.

**Template Reference:**
```text
"Workout summary description with numbers like 261 W must be in quotes"

- Free spin 5m 52%
- Warm up 10m 63%

Nx
- Work xm xx%
- Recovery xm xx%
```

**Post-Ride Nutrition Example:**
`Post-ride carbs (within 10 min): 0.5–0.6 g/kg = 48–57g`

### Step 4: Review Against Athlete Flaws
Ensure the plan does not repeat 2025 mistakes and aligns with the retrospective data:
- Is the FTP ceiling being respected? (No VO2max during early base).
- Is the recovery week actually a recovery week?
- Are the weekend rides aligned with the athlete's pure diesel physiology?
- Does the progression respect any fade or compliance issues identified in the previous block?
