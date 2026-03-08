# Forward Planning Adjustment Workflow

The AI must follow this procedure when reviewing or adjusting the training plan for the upcoming period.

**Trigger:** After weekly synthesis is complete and the user requests checking the plan for next week.

## 1. Review Existing Plan
- The current 3-week block plan was already generated. Do NOT generate an entirely new week.

## 2. Adjust based on Feedback
- Review the `workout_plans/` directory for the upcoming week.
- Read the "Next Week Recommendations" from the `commentary` blocks in the most recent `reports/YYYY/WXX/weekly_report.json`.

## 3. Subagent Invocation (`cycling-coach`) & Action
- Invoke the `cycling-coach` subagent, providing:
  - The "Next Week" recommendations from `weekly_report.json`.
  - Recent execution context from `weekly_report.json` (stats/fitness) and `coach_log.json` (qualitative notes).
  - The upcoming week's existing plan from the `workout_plans/` directory.
- Instruct the `cycling-coach` to **propose** targeted adjustments to the upcoming workouts if needed (e.g., reduce interval duration if fade was high, nudge %FTP targets up if execution was flawless). 
- **Wait for user approval.** Once the user accepts the proposed adjustments, **write** the updated plan to the corresponding file in the `workout_plans/` directory.
- Do not rewrite the plan unless adjustments are physiologically required based on recent execution.
- If adjusting format or generating new blocks, activate `session-creation` and `cycling-athlete-profile` skills.
