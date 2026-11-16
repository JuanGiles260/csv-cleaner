"""Command line interface: python -m csv_cleaner ..."""

import argparse
import sys
from pathlib import Path

from .core import clean, write


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="csv-cleaner",
        description="Merge and clean messy CSV / Excel files into one tidy file.",
    )
    p.add_argument("inputs", nargs="+", type=Path, help="Files or folders with .csv/.xlsx files")
    p.add_argument("-o", "--output", type=Path, default=Path("cleaned.csv"), help="Output .csv or .xlsx (default: cleaned.csv)")
    p.add_argument("--dates", nargs="*", default=[], help="Columns to convert to YYYY-MM-DD")
    p.add_argument("--dayfirst", action="store_true", help="Read dates like 03/04/2026 as 3 April")
    p.add_argument("--dedupe-on", nargs="*", help="Columns that identify a duplicate (default: all columns)")
    p.add_argument("--no-source", action="store_true", help="Don't add the source_file column")
    args = p.parse_args(argv)

    try:
        df, report = clean(
            args.inputs,
            date_columns=args.dates,
            dayfirst=args.dayfirst,
            dedupe_on=args.dedupe_on,
            add_source=not args.no_source,
        )
    except (ValueError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    write(df, args.output)
    print(report.summary())
    print(f"Saved to:            {args.output}")
    return 0
