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
    get_session_report_data,
    render_session_report_markdown,
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
    
    # Generate structured data
    report_data = get_session_report_data(result, fit_path.name)
    
    if args.output:
        output_path = Path(args.output)
        # Always output as JSON if output is specified, regardless of suffix
        if output_path.suffix != ".json":
            output_path = output_path.with_suffix(".json")
            
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report_data.to_dict(), indent=2), encoding="utf-8")
        print(f"Session data (JSON) written to {output_path}")
    else:
        # If no output specified, still print markdown to stdout for CLI convenience
        content = render_session_report_markdown(report_data)
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
    # Key is "YYYY-WNN" to keep years separate, but we extract labels for folder naming
    weeks: dict[str, list[tuple[Path, object]]] = defaultdict(list)
    for fit_path, result in results:
        dt = result.workout.session.start_time or datetime.now()
        iso = dt.isocalendar()
        key = f"{iso[0]}-W{iso[1]:02d}"
        weeks[key].append((fit_path, result))

    history = FitnessHistory(Path("data/fitness_history.json"))
    power_records = PowerRecords(Path("data/power_records.json"))

    summaries: list[str] = []
    for current_week_key, week_results in sorted(weeks.items()):
        # Create output directories
        year = current_week_key[:4]
        label = current_week_key[5:] # e.g., "W10"
        week_reports_dir = reports_dir / year / label
        week_reports_dir.mkdir(parents=True, exist_ok=True)

        processed_dir = fit_dir / "processed" / year / label
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Write session reports (with PR detection)
        for fit_path, result in week_results:
            dt = result.workout.session.start_time or datetime.now()
            peaks = extract_peak_powers(result.workout.records)
            pr_checks = power_records.check_prs(dt.isoformat(), peaks)
            power_records.upsert(dt.isoformat(), peaks)
            
            # Generate structured data
            report_data = get_session_report_data(result, fit_path.name, pr_checks=pr_checks)
            
            filename = session_filename(dt)
            (week_reports_dir / filename).write_text(json.dumps(report_data.to_dict(), indent=2), encoding="utf-8")

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
        
        # New JSON-first lifecycle
        from cycling_analyzer.reporter import get_weekly_report_data, render_weekly_summary_markdown
        from cycling_analyzer.models import WeeklyReportData, CommentaryBlock
        
        json_path = week_reports_dir / "weekly_report.json"
        existing_data = None
        if json_path.exists():
            try:
                raw = json.loads(json_path.read_text(encoding="utf-8"))
                # Basic migration if it was an old format, but here we assume the new one
                existing_data = raw
            except Exception:
                pass

        # Generate fresh metrics
        report_data = get_weekly_report_data(
            all_results, label,
            session_filenames=session_filenames,
            fitness_metrics=fitness_metrics,
            power_records=power_records,
        )
        
        # Merge commentary from existing JSON if present
        if existing_data and "commentary" in existing_data:
            fresh_titles = {c.title for c in report_data.commentary}
            for block_dict in existing_data["commentary"]:
                if block_dict["title"] not in fresh_titles:
                    report_data.commentary.append(CommentaryBlock(
                        title=block_dict["title"],
                        content=block_dict["content"]
                    ))

        # Save unified JSON
        json_path.write_text(json.dumps(report_data.to_dict(), indent=2), encoding="utf-8")
        
        # Generate Markdown view from the JSON
        summary_md = render_weekly_summary_markdown(report_data)
        (week_reports_dir / "weekly_summary.md").write_text(summary_md, encoding="utf-8")

        # Append code/data observations to global improvements file
        obs = collect_code_observations(all_results, label)
        if obs:
            improvements_path = Path("code_improvements.md")
            header = "# Code & Data Improvements\n\n"
            existing = improvements_path.read_text(encoding="utf-8") if improvements_path.exists() else header
            entry = f"## {current_week_key}\n\n" + "\n".join(f"- {o}" for o in obs) + "\n\n"
            if f"## {current_week_key}" not in existing:
                improvements_path.write_text(existing + entry, encoding="utf-8")

        # Archive .fit files to processed/
        for fit_path, _ in week_results:
            fit_path.rename(processed_dir / fit_path.name)

        n = len(week_results)
        summaries.append(
            f"  {current_week_key}: {n} session report{'s' if n != 1 else ''} → {week_reports_dir}/"
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
    # Key is "YYYY-WNN" to keep years separate
    weeks: dict[str, list] = defaultdict(list)
    for fit_path in all_fits:
        try:
            workout = parse_fit_file(fit_path)
            result = analyze(workout, ftp=args.ftp, weight=args.weight)
            dt = result.workout.session.start_time or datetime.now()
            iso = dt.isocalendar()
            key = f"{iso[0]}-W{iso[1]:02d}"
            weeks[key].append(result)
        except Exception as e:
            print(f"Warning: failed to parse {fit_path.name}: {e}", file=sys.stderr)

    if not weeks:
        print("No files could be parsed.", file=sys.stderr)
        sys.exit(1)

    sorted_keys = sorted(weeks.keys())
    sorted_weeks = [weeks[key] for key in sorted_keys]
    # For display in the block report, we use the WNN labels
    sorted_labels = [k[5:] for k in sorted_keys] # Extract "WNN" from "YYYY-WNN"

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

    # New JSON-first lifecycle
    from cycling_analyzer.reporter import get_block_report_data, render_block_summary_markdown
    
    report_data = get_block_report_data(
        sorted_weeks, sorted_labels,
        weekly_snapshots=snapshots_arg,
        power_records=power_records,
    )

    reports_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    year = today[:4]
    block_reports_dir = reports_dir / year / "block_reports"
    block_reports_dir.mkdir(parents=True, exist_ok=True)
    output_base = block_reports_dir / f"block_{today}"
    
    # Save JSON
    json_path = output_base.with_suffix(".json")
    json_path.write_text(json.dumps(report_data.to_dict(), indent=2), encoding="utf-8")
    
    print(f"Block analysis written to {json_path}")


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
