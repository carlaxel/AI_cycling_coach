# Cycling Power AI


## New Files
When the user says they have new files, **always follow the procedure in [Analysis Workflow](.claude/workflows/analysis-workflow.md)**.

## Workout Plans

**Always use the `cycling-coach` subagent** to design and generate workout plans, as it has the methodology knowledge required.

For the exact procedure to follow when creating a 3-week block, see **[3-Week Plan Workflow](.claude/workflows/3_week_plan_workflow.md)**.

When generating workout plan files (e.g. in `workout_plans/`):
- Each session must include an **intervals.icu workout builder block** — plain text, copy-paste ready for direct import.
- Use `%` of FTP for all power targets (never zone names), and `Nx` repeat syntax.
- Follow session structure from the athlete profile skill (warm-up, no planned cool-down).
- For full formatting rules and templates, invoke the `session-creation` skill.

## Report Generation Workflow

**For all report generation (session, weekly, block, etc.), you must follow the procedure in [Analysis Workflow](.claude/workflows/analysis-workflow.md)**.
