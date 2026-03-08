# Cycling Power AI

## Workout Plans

**Always use the `cycling-coach` subagent** to design and generate workout plans, as it has the methodology knowledge required.

For the exact procedure to follow when creating a 3-week block, see **[3-Week Plan Workflow](.claude/workflows/3_week_plan_workflow.md)**.

When generating workout plan files (e.g. in `workout_plans/`):
- Each session must include an **intervals.icu workout builder block** — plain text, copy-paste ready for direct import.
- Use `%` of FTP for all power targets (never zone names), and `Nx` repeat syntax.
- Follow session structure from the athlete profile skill (warm-up, no planned cool-down).
- For full formatting rules and templates, invoke the `session-creation` skill.

## Phase 1: Session Analysis
**Trigger:** The user drops new `.fit` file(s) and says "I have new files."
- **Workflow:** Strictly follow the **[Session Analysis Workflow](.claude/workflows/session-analysis.md)** to ingest, analyze, and enrich the new session files with coaching notes.

## Phase 2: Weekly Critique
**Trigger:** The user requests the weekly wrap-up (usually on Sunday).
- **Workflow:** Follow the **[Weekly Critique Workflow](.claude/workflows/weekly-critique.md)** to roll up the week's data, assess fatigue, and generate a coaching critique for the week.

## Phase 3: Planning Adjustment
**Trigger:** After weekly synthesis or when checking the plan for next week.
- **Workflow:** Use the **[Forward Planning Adjustment Workflow](.claude/workflows/planning-adjustment.md)** to propose and apply targeted adjustments to the upcoming training plan based on recent performance.

## Phase 4: Block Retrospective
**Trigger:** End of a 3-4 week training block or when running `report.py block`.
- **Workflow:** Follow the **[Block Retrospective Workflow](.claude/workflows/block-retrospective.md)** to gather macro data, review physiological trends, and perform historical block comparisons.
