# Cycling Analysis Workflow

The AI must strictly follow this 4-Phase sequence of operations when interacting with cycling data.

## Phase 1: Ingestion, Analysis & Qualitative Enrichment
**Trigger:** The user drops new `.fit` file(s) and says "I have new files."

1. **Ingestion & Raw Generation:**
   - Run `./inbox.sh` to move `.fit` files to `fit_files/unprocessed/`.
   - Run `uv run python report.py week` to process all new files, generate the raw `session_YYYY-MM-DD.md` reports, and update/create the `weekly_summary.md` in the `reports/YYYY/YYYY-WXX/` directory.
   - *Note on `.gitignore`:* The `reports/` and `workout_plans/` directories are ignored by git. You must disable gitignore filtering in your file/search tools (e.g., set `respect_git_ignore: false` or `no_ignore: true`) or use shell commands (`ls`, `cat`, `find`) to view them.

2. **Intent & Compliance Check:**
   - Activate the `cycling-athlete-profile` skill to establish the athlete's current FTP, weight, and power zones.
   - Search the `workout_plans/` directory (or workspace root) for the active training plan (files are typically structured as 3-week blocks or single-week plans, e.g., `YYYY_monthXX-XXmd`).
   - Locate the specific day's prescribed workout within the active plan (with matching dates).
   - Compare executed laps against prescribed `intervals.icu` blocks (did they hit W/kg or %FTP targets? duration? recovery?).
3. **Skill-Based Deep Dive:**
   - **For Structured Work (SST, Threshold, VO2Max):** Activate `interval-execution-analysis` skill to calculate Fade Index, Cardiac Drift, and evaluate CV (pacing consistency).
   - **For Endurance / Z2:** Activate `heart-rate-aerobic-efficiency` skill to evaluate Aerobic Decoupling (Pw:HR, 5% rule) and check for "The Muddle".
4. **Block Context & Progression:**
   - Search recent session files (from the current 3-week block) for similar workouts.
   - Compare the physiological response (e.g., changes in EF, fade, or decoupling compared to last week).
5. **Permanent Enrichment (via `cycling-coach`):**
   - Invoke the `cycling-coach` subagent and provide it with the generated session metrics, the calculated deep-dive skill data (Fade Index, Decoupling, etc.), and the day's intended plan.
   - Instruct the `cycling-coach` to append a standardized **"Qualitative Analysis & Coach's Notes"** section directly to the bottom of the newly generated `session_*.md` file.
   - **Include:** 1. Plan Compliance, 2. Execution Quality (applying IF/TSS/Muddle rules), 3. Physiological Response & Block Context.

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
   - Instruct the `cycling-coach` to propose targeted adjustments to the upcoming workouts if needed (e.g., reduce interval duration if fade was high, nudge %FTP targets up if execution was flawless). 
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
   - Activate `heart-rate-aerobic-efficiency` and `interval-execution-analysis` to evaluate macro trends (e.g., has decoupling stabilized over the block? Did execution quality improve?).
4. **Historical Block Comparison:**
   - Locate previous block reports (e.g., in `reports/YYYY/`).
   - Read up to the 5 most recent block reports to establish a longitudinal baseline for progression, fatigue tolerance, and phenotypic shifts.
5. **Subagent Invocation (`cycling-coach`) & Block Report Generation:**
   - Activate the `cycling-athlete-profile` skill to provide context on long-term goals and philosophy.
   - Feed PMC data, macro trends, PRs, and the historical block comparison to the `cycling-coach` subagent.
   - The subagent writes a comprehensive **Block Report**, detailing the retrospective analysis, comparative progress, and dictating the strategy for the next mesocycle.
   - If a new block plan needs to be generated, activate the `session-creation` skill to draft the upcoming workouts based on the strategy.
