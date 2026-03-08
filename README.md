# AI Cycling Coach

A Python tool for analysing cycling `.fit` files and generating structured training reports — session analyses, weekly summaries, and multi-week block analyses — designed to work alongside Claude as an AI coaching assistant.

## What it does

- **Parses `.fit` files** from cycling computers and smartwatches (power, HR, cadence, speed, GPS, pedaling dynamics)
- **Computes training metrics**: Normalised Power (NP), Intensity Factor (IF), Training Stress Score (TSS), W/kg, power zone distribution
- **Tracks fitness over time** using a CTL/ATL/TSB performance management model (42-day / 7-day EMAs)
- **Generates markdown reports**:
  - Per-session analysis with lap breakdown and power distribution
  - Weekly summary with aggregate load, fitness trend, and coaching critique
  - Multi-week block analysis across all accumulated data

## Project structure

```
cycling_power_ai/
├── cycling_analyzer/       # Core Python package
│   ├── parser.py           # FIT file parser (fitdecode)
│   ├── analyzer.py         # Metric computation (NP, IF, TSS, zones)
│   ├── fitness_model.py    # CTL/ATL/TSB performance management chart
│   ├── formatter.py        # Text and JSON output formatters
│   ├── reporter.py         # Markdown report generators
│   ├── models.py           # Data classes (WorkoutData, SessionSummary, etc.)
│   └── utils.py
├── report.py               # CLI: generate session, week, and block reports
├── analyze.py              # CLI: quick analysis of a single .fit file
├── inbox.sh                # Helper: move .fit files from ~/Downloads into fit_files/unprocessed/
├── pyproject.toml
├── uv.lock
├── athlete.json            # ← NOT included (personal data — create manually, see below)
├── fit_files/              # ← NOT included (personal data — create manually, see below)
│   ├── unprocessed/        #   Drop new .fit files here
│   └── processed/          #   Files archived here after report generation
├── data/                   # ← NOT included (generated — created automatically on first run)
│   └── fitness_history.json
└── reports/                # ← NOT included (generated — created automatically)
    └── YYYY/
        ├── WNN/
        │   ├── session_YYYY-MM-DD.md
        │   └── weekly_summary.md
        └── block_reports/
            └── block_YYYY-MM-DD.json
```

## Setup

### Prerequisites

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv)

### Install

```bash
uv sync
```

### Files you need to create

Two things are excluded from this repo because they contain personal data:

#### 1. `athlete.json`

Create this file at the project root. It stores your FTP and weight, which are used as defaults for all report commands so you don't have to pass flags every time.

```json
{
  "ftp": 250,
  "weight_kg": 70.0
}
```

Without this file, you must pass `--ftp` and `--weight` explicitly to every command.

#### 2. `fit_files/` directory

```bash
mkdir -p fit_files/unprocessed fit_files/processed
```

Drop `.fit` files exported from your cycling computer or Garmin Connect into `fit_files/unprocessed/` before running `report.py week`.

## Usage

### Quick single-file analysis (stdout)

```bash
uv run python analyze.py path/to/activity.fit --ftp 250 --weight 70
uv run python analyze.py path/to/activity.fit --json   # JSON output
```

### Generate reports from inbox

```bash
# 1. Move .fit files from ~/Downloads into fit_files/unprocessed/
./inbox.sh

# 2. Generate session reports + weekly summary
uv run python report.py week

# 3. Generate a training block analysis (all accumulated weeks)
uv run python report.py block
```

### Single-file session report

```bash
uv run python report.py session path/to/activity.fit --output reports/my_session.md
```

### CLI flags

All `report.py` subcommands accept:

| Flag | Default | Description |
|---|---|---|
| `--ftp` | from `athlete.json` | FTP in watts |
| `--weight` | from `athlete.json` | Rider weight in kg |
| `--fit-dir` | `fit_files` | Root directory for `.fit` files |
| `--reports-dir` | `reports` | Output directory for reports |

## Claude integration

This project includes Claude agent/skill definitions under `.claude/`:

- **`agents/cycling-coach.md`** — coaching subagent invoked for weekly summaries and block analysis
- **`skills/fitness-fatigue-model/`** — CTL/ATL/TSB methodology reference
- **`skills/interval-execution-analysis/`** — interval execution quality analysis
- **`skills/session-creation/`** — workout plan formatting rules

The `CLAUDE.md` file at the project root describes the full report generation workflow and when to invoke each skill.

## Dependencies

| Package | Purpose |
|---|---|
| `fitdecode` | Parse binary `.fit` files |
| `pandas` | Data aggregation and time-series manipulation |
