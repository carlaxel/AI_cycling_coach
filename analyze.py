#!/usr/bin/env python3
"""CLI entry point for cycling FIT file analysis."""

import argparse
import sys
from pathlib import Path

from cycling_analyzer import analyze, format_json, format_text, parse_fit_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze a cycling .fit file and display workout metrics."
    )
    parser.add_argument("file", type=Path, help="Path to the .fit file")
    parser.add_argument("--ftp", type=int, default=None, help="Your FTP in watts")
    parser.add_argument("--weight", type=float, default=None, help="Rider weight in kg")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        workout = parse_fit_file(args.file)
    except ValueError as e:
        print(f"Error parsing FIT file: {e}", file=sys.stderr)
        sys.exit(1)

    result = analyze(workout, ftp=args.ftp, weight=args.weight)

    if args.json:
        print(format_json(result))
    else:
        print(format_text(result))


if __name__ == "__main__":
    main()
