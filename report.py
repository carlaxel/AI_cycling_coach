#!/usr/bin/env python3
"""CLI entry point for generating weekly reports and training block analysis."""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from cycling_analyzer import analyze, parse_fit_file
from cycling_analyzer.fitness_model import FitnessHistory
from cycling_analyzer.power_records import PowerRecords, extract_peak_powers
from cycling_analyzer.reporter import (
    session_filename,
    week_label,
    collect_code_observations,
    generate_block_analysis,
    generate_session_report,
    generate_weekly_summary,
)


def cmd_session(args: argparse.Namespace) -> None:
    fit_path = Path(args.file)
    if not fit_path.exists():
        print(f"Error: file not found: {fit_path}", file=sys.stderr)
        sys.exit(1)

    try:
        workout = parse_fit_file(fit_path)
    except ValueError as e:
        print(f"Error parsing FIT file: {e}", file=sys.stderr)
        sys.exit(1)

    result = analyze(workout, ftp=args.ftp, weight=args.weight)
    content = generate_session_report(result, fit_path.name)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"Session report written to {output_path}")
    else:
        print(content)


def cmd_week(args: argparse.Namespace) -> None:
    fit_dir = Path(args.fit_dir)
    reports_dir = Path(args.reports_dir)

    inbox_dir = fit_dir / "unprocessed"
    fit_files = sorted(inbox_dir.glob("*.fit"))
    if not fit_files:
        print(f"No .fit files found in {inbox_dir}/")
        print("Drop your .fit files into the fit_files/unprocessed/ directory and try again.")
        sys.exit(0)

    # Parse and analyze
    results: list[tuple[Path, object]] = []
    for fit_path in fit_files:
        try:
            workout = parse_fit_file(fit_path)
            result = analyze(workout, ftp=args.ftp, weight=args.weight)
            results.append((fit_path, result))
        except Exception as e:
            print(f"Warning: failed to parse {fit_path.name}: {e}", file=sys.stderr)

    if not results:
        print("No files could be parsed.", file=sys.stderr)
        sys.exit(1)

    # Group results by their actual ISO week
    weeks: dict[str, list[tuple[Path, object]]] = defaultdict(list)
    for fit_path, result in results:
        dt = result.workout.session.start_time
        label = week_label(dt) if dt else week_label(datetime.now())
        weeks[label].append((fit_path, result))

    history = FitnessHistory(Path("data/fitness_history.json"))
    power_records = PowerRecords(Path("data/power_records.json"))

    summaries: list[str] = []
    for current_week, week_results in sorted(weeks.items()):
        # Create output directories
        year = current_week[:4]
        week_reports_dir = reports_dir / year / current_week
        week_reports_dir.mkdir(parents=True, exist_ok=True)

        processed_dir = fit_dir / "processed" / current_week
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Write session reports (with PR detection)
        for fit_path, result in week_results:
            dt = result.workout.session.start_time or datetime.now()
            peaks = extract_peak_powers(result.workout.records)
            pr_checks = power_records.check_prs(dt.isoformat(), peaks)
            power_records.upsert(dt.isoformat(), peaks)
            filename = session_filename(dt)
            content = generate_session_report(result, fit_path.name, pr_checks=pr_checks)
            (week_reports_dir / filename).write_text(content, encoding="utf-8")

        # Include already-archived .fit files for the same week in the summary
        extra_results: list[object] = []
        new_fit_names = {fit_path.name for fit_path, _ in week_results}
        for archived_fit in sorted(processed_dir.glob("*.fit")):
            if archived_fit.name in new_fit_names:
                continue
            try:
                workout = parse_fit_file(archived_fit)
                extra_result = analyze(workout, ftp=args.ftp, weight=args.weight)
                extra_results.append(extra_result)
                # Upsert archived session peaks (idempotent)
                arc_dt = extra_result.workout.session.start_time
                if arc_dt:
                    arc_peaks = extract_peak_powers(extra_result.workout.records)
                    power_records.upsert(arc_dt.isoformat(), arc_peaks)
            except Exception as e:
                print(f"Warning: failed to parse archived {archived_fit.name}: {e}", file=sys.stderr)

        all_results = extra_results + [r for _, r in week_results]
        all_results.sort(key=lambda r: r.workout.session.start_time or datetime.min)

        # Update fitness history with all sessions for this week (idempotent upserts)
        for result in all_results:
            dt = result.workout.session.start_time
            if dt and result.tss is not None:
                history.upsert(dt.isoformat(), result.tss)

        # Compute fitness metrics as of the last session date this week
        week_dates = [r.workout.session.start_time for r in all_results if r.workout.session.start_time]
        fitness_metrics = history.compute_metrics(max(week_dates).date()) if week_dates else None

        session_filenames = [
            session_filename(r.workout.session.start_time or datetime.now())
            for r in all_results
        ]
        summary = generate_weekly_summary(
            all_results, current_week,
            session_filenames=session_filenames,
            fitness_metrics=fitness_metrics,
            power_records=power_records,
        )
        (week_reports_dir / "weekly_summary.md").write_text(summary, encoding="utf-8")

        # Append code/data observations to global improvements file
        obs = collect_code_observations(all_results, current_week)
        if obs:
            improvements_path = Path("code_improvements.md")
            header = "# Code & Data Improvements\n\n"
            existing = improvements_path.read_text(encoding="utf-8") if improvements_path.exists() else header
            entry = f"## {current_week}\n\n" + "\n".join(f"- {o}" for o in obs) + "\n\n"
            if f"## {current_week}" not in existing:
                improvements_path.write_text(existing + entry, encoding="utf-8")

        # Archive .fit files to processed/
        for fit_path, _ in week_results:
            fit_path.rename(processed_dir / fit_path.name)

        n = len(week_results)
        summaries.append(
            f"  {current_week}: {n} session report{'s' if n != 1 else ''} → {week_reports_dir}/"
        )

    history.save()
    power_records.save()

    print(f"Generated reports for {len(weeks)} week(s):")
    for s in summaries:
        print(s)


def cmd_block(args: argparse.Namespace) -> None:
    fit_dir = Path(args.fit_dir)
    reports_dir = Path(args.reports_dir)

    processed_dir = fit_dir / "processed"
    inbox_dir = fit_dir / "unprocessed"
    all_fits: list[Path] = []
    if processed_dir.exists():
        all_fits.extend(processed_dir.rglob("*.fit"))
    if inbox_dir.exists():
        all_fits.extend(inbox_dir.glob("*.fit"))

    if not all_fits:
        print(f"No .fit files found in {inbox_dir}/ or {processed_dir}/")
        sys.exit(0)

    # Parse, analyze, group by ISO week
    weeks: dict[str, list] = defaultdict(list)
    for fit_path in all_fits:
        try:
            workout = parse_fit_file(fit_path)
            result = analyze(workout, ftp=args.ftp, weight=args.weight)
            dt = result.workout.session.start_time or datetime.now()
            weeks[week_label(dt)].append(result)
        except Exception as e:
            print(f"Warning: failed to parse {fit_path.name}: {e}", file=sys.stderr)

    if not weeks:
        print("No files could be parsed.", file=sys.stderr)
        sys.exit(1)

    sorted_labels = sorted(weeks.keys())
    sorted_weeks = [weeks[label] for label in sorted_labels]

    # Build/update fitness history and power records from all sessions
    history = FitnessHistory(Path("data/fitness_history.json"))
    power_records = PowerRecords(Path("data/power_records.json"))
    for week_results in sorted_weeks:
        for result in week_results:
            dt = result.workout.session.start_time
            if dt and result.tss is not None:
                history.upsert(dt.isoformat(), result.tss)
            if dt:
                peaks = extract_peak_powers(result.workout.records)
                power_records.upsert(dt.isoformat(), peaks)
    history.save()
    power_records.save()

    # Compute per-week fitness snapshots (as of each week's last session date)
    weekly_snapshots = []
    for week_results in sorted_weeks:
        dates = [r.workout.session.start_time for r in week_results if r.workout.session.start_time]
        if dates:
            weekly_snapshots.append(history.snapshot(max(dates).date()))
        else:
            weekly_snapshots.append(None)
    # Only pass if all weeks have snapshots
    snapshots_arg = weekly_snapshots if all(s is not None for s in weekly_snapshots) else None

    report = generate_block_analysis(
        sorted_weeks, sorted_labels,
        weekly_snapshots=snapshots_arg,
        power_records=power_records,
    )

    reports_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    year = today[:4]
    output_path = reports_dir / year / f"block_{today}.md"
    (reports_dir / year).mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print(f"Block analysis written to {output_path}")


def _load_athlete() -> dict:
    path = Path(__file__).parent / "athlete.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def main() -> None:
    athlete = _load_athlete()
    default_weight = athlete.get("weight_kg")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--ftp", type=int, default=athlete.get("ftp"), help="Your FTP in watts (default: from athlete.json)")
    common.add_argument("--weight", type=float, default=default_weight, help="Rider weight in kg (default: from athlete.json)")
    common.add_argument(
        "--fit-dir",
        default="fit_files",
        help="Directory containing .fit files (default: fit_files)",
    )
    common.add_argument(
        "--reports-dir",
        default="reports",
        help="Directory for output reports (default: reports)",
    )

    parser = argparse.ArgumentParser(
        description="Generate cycling training reports from .fit files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    session_p = subparsers.add_parser(
        "session",
        help="Generate a markdown report for a single .fit file",
    )
    session_p.add_argument("file", type=str, help="Path to the .fit file")
    session_p.add_argument("--ftp", type=int, default=athlete.get("ftp"), help="Your FTP in watts (default: from athlete.json)")
    session_p.add_argument("--weight", type=float, default=default_weight, help="Rider weight in kg (default: from athlete.json)")
    session_p.add_argument("--output", type=str, default=None, help="Write report to this file instead of stdout")
    session_p.set_defaults(func=cmd_session)

    week_p = subparsers.add_parser(
        "week",
        parents=[common],
        help="Generate per-session and weekly summary reports",
    )
    week_p.set_defaults(func=cmd_week)

    block_p = subparsers.add_parser(
        "block",
        parents=[common],
        help="Generate training block analysis across all processed weeks",
    )
    block_p.set_defaults(func=cmd_block)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
