# Cycling Power AI

## Training Context

Use the following skills for domain context when working on this project:

- **`cycling-athlete-profile`** — athlete dimensions, FTP, power zones, goals and philosophy
- **`cycling-coach`** (subagent) — use this agent when analyzing training metrics, sessions, fatigue, or making methodology decisions.


## New Files
When the user says they have new files:
1. Run `./inbox.sh` to move `.fit` files from `~/Downloads/` into `fit_files/unprocessed/` (overwrites duplicates)
2. Count the files and decide what to generate:
   - **Multiple files** → always run the full week report (session files + weekly summary)
   - **Single file** → generate session file only; also generate weekly summary if today is Sunday (week starts on Monday)

## Workout Plans

When generating workout plan files (e.g. in `workout_plans/`):
- Each session must include an **intervals.icu workout builder block** — plain text, copy-paste ready for direct import.
- Use `%` of FTP for all power targets (never zone names), and `Nx` repeat syntax.
- Follow session structure from the athlete profile skill (warm-up, no planned cool-down).
- For full formatting rules and templates, invoke the `session-creation` skill.

## Report Generation Workflow

### Session only
```
uv run python report.py week
```
_(generates session files and, when applicable, the weekly summary)_

### Block analysis (run after multiple weeks are accumulated)
```
uv run python report.py block
```

### Weekly summary content rules
- Always invoke the **`cycling-coach`** subagent to write the weekly summary — it has the methodology knowledge to produce meaningful critique and insights
- Always generate individual session files first, then generate the weekly summary
- **Before invoking the cycling-coach subagent**, read every session file for the week from disk and include the exact filenames (including the `HH-MM` timestamp) and real metrics in the prompt. Never approximate or guess session timestamps — they encode the recording start time and cannot be inferred. Fabricating session data is a critical error.
- The weekly summary must include a one-sentence description of each session with a relative link to its session file (e.g. `[2026-02-23](session_2026-02-23_10-00.md)`)
- Pull insights from the session files that the aggregate metrics don't capture (e.g. execution quality, pacing, notable power distribution, or training remarks) and include them in the weekly summary
- Session order in the summary: chronological
- End the weekly summary with two separate sections:
  - **Critique**: honest assessment of the week's training quality and execution — at least one point, as many as are genuinely useful
  - **Insights**: patterns, trends, or observations worth noting for future training — at least one point, as many as are genuinely useful
  - **Next Week**: (optional) one concrete improvement task if there is something actionable worth highlighting — omit if nothing stands out
