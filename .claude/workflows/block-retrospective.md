# Block Retrospective Workflow

The AI must follow this procedure at the end of a training block or when a high-level summary is requested.

**Trigger:** End of a 3-4 week block, or when the user runs `report.py block`.

## 1. Macro Data Gathering
- Run `uv run python report.py block`.
- Run `uv run pr_report.py` to extract all Power PRs from the block.

## 2. Deep Phenotype Review
- Activate `power-duration-profiling` skill to check for FTP Staleness and evaluate 5-sec to 5-min to 20-min phenotype ratios and period bests.

## 3. Macro Fatigue & Efficiency Review
- Activate `fitness-fatigue-model` skill to review the 4-week CTL trend and ATL levels to assess base building and need for deload.
- Activate `heart-rate-aerobic-efficiency` and `interval-execution-analysis` to evaluate macro trends across the weekly reports (reading `weekly_report.json` and `coach_log.json` for each week in the block).
- Check if Interval Decoupling (Pw:HR) stabilized, and if Fade Index and Target Compliance improved by reviewing the session-level JSON data and coach's notes.

## 4. Historical Block Comparison
- Locate previous block reports (e.g., in `reports/YYYY/block_reports/`).
- Activate the `session-matching` skill to establish a longitudinal baseline for progression, fatigue tolerance, and phenotypic shifts across repeated workout formats from up to the 5 most recent block reports.

## 5. Subagent Invocation (`cycling-coach`) & Block Report Generation
- Activate the `cycling-athlete-profile` skill to provide context on long-term goals and philosophy.
- Feed PMC data, macro trends, PRs, and the historical block comparison to the `cycling-coach` subagent.
- The subagent writes a comprehensive **Block Report** (to `reports/YYYY/block_reports/block_*.md`), detailing the retrospective analysis, comparative progress, and dictating the strategy for the next mesocycle.
