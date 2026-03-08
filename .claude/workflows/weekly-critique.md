# Weekly Critique Workflow

The AI must follow this procedure to synthesize a week of training and provide coaching feedback.

**Trigger:** The user requests the weekly wrap-up (usually on Sunday).

## 1. Data Roll-Up
- Read the `weekly_report.json` for the week to gather all automated stats, PMC data, and existing takeaways.
- Read the `coach_log.json` file for the week to gather all per-session "Qualitative Analysis & Coach's Notes".

## 2. Fatigue & Load Assessment
- Activate `fitness-fatigue-model` skill to evaluate CTL ramp rate (target 3–7 pts/week) and ending TSB (Form). Check for appropriate fatigue vs. overreaching using the data from `weekly_report.json`.

## 3. Permanent Enrichment (via `cycling-coach`)
- Activate the `cycling-athlete-profile` skill to establish the athlete's goals, FTP, weight, and training philosophy.
- Locate the active 3-week training plan and summarize it into a simplified format (focusing on key workouts, target progressions, and block goals).
- Provide the structured `weekly_report.json` data, the per-session `coach_log.json` analysis, athlete profile context, and the summarized 3-week plan to the `cycling-coach` subagent.
- The subagent writes the **Weekly Critique** as a set of structured `CommentaryBlock` objects (e.g., "Critique," "Insights," "Next Week Recommendations").
- **Update Procedure:**
  1. Read the existing `weekly_report.json`.
  2. Update the `commentary` array with the new `CommentaryBlock` objects (each having a `title` and `content` string).
  3. Ensure other keys in the JSON (summary, fitness, peaks, etc.) are preserved.
  4. Write the updated data back to `weekly_report.json`.
- Trigger a re-generation of `weekly_summary.md` by running `uv run python report.py week`.
