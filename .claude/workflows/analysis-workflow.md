# Cycling Analysis Workflow

The AI must strictly follow this 4-Phase sequence of operations when interacting with cycling data.

## Phase 1: Ingestion, Analysis & Qualitative Enrichment
**Trigger:** The user drops new `.fit` file(s) and says "I have new files."

1. **Ingestion & Raw Generation:**
   - Run `./inbox.sh` to move `.fit` files to `fit_files/unprocessed/`.
   - Run `uv run python report.py week` to process all new files, generate the raw `session_YYYY-MM-DD.md` reports, and update/create the `weekly_summary.md` in the `reports/YYYY/YYYY-WXX/` directory.

2. **Intent & Compliance Check:**
   - Activate the `cycling-athlete-profile` skill to establish the athlete's current FTP, weight, and power zones.
   - Search the `workout_plans/` directory for the active training plan (files are typically structured as 3-week blocks or single-week plans, e.g., `YYYY_monthXX-XX.md`) with a date range overlapping the current date.
   - Locate the specific day's prescribed workout within the active plan (with matching dates).
   - **Extract "Soft Targets":** Identify target HR range, cadence targets, and the stated "Purpose" of the session (e.g., "Mitochondrial density," "Consolidating aerobic base").
   - **Check Completeness:** Verify if all planned sessions for the week-to-date have been executed. Identify any "Extra" (unplanned) or "Missed" rides.
   - Compare executed laps (from `session_*.md`) against prescribed `intervals.icu` blocks (did they hit W/kg or %FTP targets? duration? recovery?).

3. **Skill-Based Deep Dive & Verification:**
   - **Verification:** Review the automated "Interval Execution Analysis" in the `session_*.md` file. Verify if it correctly identified intervals and metrics like Fade, CV, and Drift.
   - **Environmental Context:** Note the "Venue" (Indoor/Outdoor). For Indoor rides, remember that HR is typically 3–10 bpm lower than outdoor at the same power.
   - **For Structured Work (SST, Threshold, VO2Max):** Activate `interval-execution-analysis` skill to calculate Fade Index, Cardiac Drift, and evaluate CV (pacing consistency).
   - **For Endurance / Z2:** Activate `heart-rate-aerobic-efficiency` skill to evaluate Aerobic Decoupling (Pw:HR, 5% rule) and check for "The Muddle" (riding in Z3/Tempo when Z2 was prescribed).

4. **Block Context & Progression:**
   - Activate the `session-matching` skill to search recent session files to find up to the **last 3 similar workouts** (even if they fall outside the current block).
   - Use the skill's rules to fingerprint and compare the physiological response (e.g., changes in EF, fade, or decoupling).
   - **For quality sessions (e.g., VO2Max, Threshold, SST):** explicitly focus the matching and comparison effort on the **work intervals**, as they dictate the primary adaptation.

5. **Permanent Enrichment (via `cycling-coach`):**
   - Invoke the `cycling-coach` subagent and provide it with a comprehensive data package:
     - **Automated Stats:** Generated session metrics (NP, IF, TSS, EF, Decoupling) and Interval Execution metrics (Fade, CV, Drift).
     - **Plan Intent:** Purpose, Soft Targets (HR, Cadence), and Interval targets.
     - **Context:** Venue (Indoor/Outdoor), Block progression (how this compares to previous same-type sessions), and any Subjective Feel/RPE (if provided by user).
   - Instruct the `cycling-coach` to synthesize this into a standardized **"Qualitative Analysis & Coach's Notes"** section and append it directly to the bottom of the newly generated `session_*.md` file.
   - **Include:** 
     1. **Plan Compliance:** (Target Power vs. Actual, Target HR vs. Actual).
     2. **Execution Quality:** (Applying IF/TSS/Muddle rules, pacing consistency).
     3. **Physiological Response:** (Cardiac drift context, EF trend, fatigue indication).
     4. **Block Context:** (Progression from previous sessions, adaptation notes).

## Phase 2: Weekly Synthesis & Coaching Critique
**Trigger:** Phase 1 is complete and the user requests the weekly wrap-up (usually on Sunday).

1. **Data Roll-Up:** 
   - Read the `session_*.md` files for the week, focusing on the pre-computed "Qualitative Analysis & Coach's Notes", and the `weekly_summary.md`.
2. **Fatigue & Load Assessment:** 
   - Activate `fitness-fatigue-model` skill to evaluate CTL ramp rate (target 3–7 pts/week) and ending TSB (Form). Check for appropriate fatigue vs. overreaching.
3. **Subagent Invocation (`cycling-coach`):**
   - Activate the `cycling-athlete-profile` skill to establish the athlete's goals, FTP, weight, and training philosophy.
   - Locate the active 3-week training plan and summarize it into a simplified format (focusing on key workouts, target progressions, and block goals).
   - Provide the week's qualitative session notes, the automated `weekly_summary.md` stats, PMC data, athlete profile context, and the summarized 3-week plan to the `cycling-coach` subagent.
   - The subagent writes the **Weekly Critique** (must include chronological links to sessions, Critique, Insights, and Next Week recommendations) and appends it to the bottom of the `weekly_summary.md`.

## Phase 3: Forward Planning Adjustment
**Trigger:** After weekly synthesis is complete and the user requests checking the plan for next week.

1. **Review Existing Plan:** 
   - The current 3-week block plan was already generated. Do NOT generate an entirely new week.
2. **Adjust based on Feedback:** 
   - Review the `workout_plans/` directory for the upcoming week based on the "Next Week" recommendations from Phase 2.
3. **Subagent Invocation (`cycling-coach`) & Action:** 
   - Invoke the `cycling-coach` subagent, providing the "Next Week" recommendations, recent execution context, and the upcoming week's plan.
   - Instruct the `cycling-coach` to **propose** targeted adjustments to the upcoming workouts if needed (e.g., reduce interval duration if fade was high, nudge %FTP targets up if execution was flawless). 
   - **Wait for user approval.** Once the user accepts the proposed adjustments, **write** the updated plan to the corresponding file in the `workout_plans/` directory.
   - Do not rewrite the plan unless adjustments are physiologically required based on recent execution.
   - If adjusting format or generating new blocks, activate `session-creation` and `cycling-athlete-profile` skills.

## Phase 4: Block / Phase Retrospective
**Trigger:** End of a 3-4 week block, or when the user runs `report.py block`.

1. **Macro Data Gathering:**
   - Run `uv run python report.py block`.
   - Run `uv run pr_report.py` to extract all Power PRs from the block.
2. **Deep Phenotype Review:** 
   - Activate `power-duration-profiling` skill to check for FTP Staleness and evaluate 5-sec to 5-min to 20-min phenotype ratios and period bests.
3. **Macro Fatigue & Efficiency Review:** 
   - Activate `fitness-fatigue-model` skill to review the 4-week CTL trend and ATL levels to assess base building and need for deload.
   - Activate `heart-rate-aerobic-efficiency` and `interval-execution-analysis` to evaluate macro trends across the weekly summary tables (e.g., has Interval Decoupling (Pw:HR) stabilized over the block? Did Fade Index and Target Compliance improve?).
4. **Historical Block Comparison:**
   - Locate previous block reports (e.g., in `reports/YYYY/`).
   - Activate the `session-matching` skill to establish a longitudinal baseline for progression, fatigue tolerance, and phenotypic shifts across repeated workout formats from up to the 5 most recent block reports.
5. **Subagent Invocation (`cycling-coach`) & Block Report Generation:**
   - Activate the `cycling-athlete-profile` skill to provide context on long-term goals and philosophy.
   - Feed PMC data, macro trends, PRs, and the historical block comparison to the `cycling-coach` subagent.
   - The subagent writes a comprehensive **Block Report**, detailing the retrospective analysis, comparative progress, and dictating the strategy for the next mesocycle.
