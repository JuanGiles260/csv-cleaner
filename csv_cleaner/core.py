"""Cleaning logic. Every step is a small function so it can be tested and reused."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

SUPPORTED = {".csv", ".xlsx", ".xls"}


@dataclass
class Report:
    files: list[str] = field(default_factory=list)
    rows_in: int = 0
    empty_rows_removed: int = 0
    duplicates_removed: int = 0
    rows_out: int = 0
    columns: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return "\n".join(
            [
                f"Files merged:        {len(self.files)}",
                f"Rows read:           {self.rows_in}",
                f"Empty rows removed:  {self.empty_rows_removed}",
                f"Duplicates removed:  {self.duplicates_removed}",
                f"Rows written:        {self.rows_out}",
                f"Columns:             {', '.join(self.columns)}",
            ]
        )


def normalize_header(name: object) -> str:
    """'  Customer Name ' -> 'customer_name', 'E-mail' -> 'e_mail'."""
    text = str(name).strip().lower()
    text = re.sub(r"[^\w]+", "_", text)
    return text.strip("_") or "column"


def dedupe_headers(headers: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for h in headers:
        if h in seen:
            seen[h] += 1
            out.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            out.append(h)
    return out


def read_file(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        # sep=None lets pandas detect ',' ';' or tab; utf-8-sig drops Excel's BOM.
        return pd.read_csv(path, sep=None, engine="python", dtype=str, encoding="utf-8-sig")
    return pd.read_excel(path, dtype=str)


def strip_text(df: pd.DataFrame) -> pd.DataFrame:
    """Trim spaces, collapse inner whitespace and turn blank strings into NaN."""
    def clean(value):
        if isinstance(value, str):
            value = re.sub(r"\s+", " ", value).strip()
            return value if value else pd.NA
        return value

    return df.apply(lambda col: col.map(clean))


def parse_dates(df: pd.DataFrame, columns: list[str], dayfirst: bool) -> pd.DataFrame:
    """Convert the given columns to ISO dates (YYYY-MM-DD). Unparseable values are kept as-is."""
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            raise KeyError(f"Date column '{col}' not found. Available: {', '.join(df.columns)}")
        values = df[col]
        # ISO dates (2026-09-05) are unambiguous: never apply dayfirst to them.
        iso = values.astype("string").str.match(r"^\d{4}-\d{1,2}-\d{1,2}", na=False)
        parsed = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
        parsed[iso] = pd.to_datetime(values[iso], errors="coerce", format="mixed")
        parsed[~iso] = pd.to_datetime(values[~iso], errors="coerce", dayfirst=dayfirst, format="mixed")
        df[col] = parsed.dt.strftime("%Y-%m-%d").where(parsed.notna(), df[col])
    return df


def collect_files(inputs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in inputs:
        if p.is_dir():
            files.extend(sorted(f for f in p.iterdir() if f.suffix.lower() in SUPPORTED))
        elif p.suffix.lower() in SUPPORTED:
            files.append(p)
        else:
            raise ValueError(f"Unsupported file: {p}")
    if not files:
        raise ValueError("No CSV or Excel files found.")
    return files


def clean(
    inputs: list[Path],
    date_columns: list[str] | None = None,
    dayfirst: bool = False,
    dedupe_on: list[str] | None = None,
    add_source: bool = True,
) -> tuple[pd.DataFrame, Report]:
    report = Report()
    frames = []
    for path in collect_files(inputs):
        df = read_file(path)
        df.columns = dedupe_headers([normalize_header(c) for c in df.columns])
        if add_source:
            df["source_file"] = path.name
        frames.append(df)
        report.files.append(path.name)
        report.rows_in += len(df)

    df = pd.concat(frames, ignore_index=True, sort=False)
    df = strip_text(df)

    data_cols = [c for c in df.columns if c != "source_file"]
    before = len(df)
    df = df.dropna(how="all", subset=data_cols)
    report.empty_rows_removed = before - len(df)

    if date_columns:
        df = parse_dates(df, [normalize_header(c) for c in date_columns], dayfirst)

    before = len(df)
    subset = [normalize_header(c) for c in dedupe_on] if dedupe_on else data_cols
    df = df.drop_duplicates(subset=subset, keep="first")
    report.duplicates_removed = before - len(df)

    df = df.reset_index(drop=True)
    report.rows_out = len(df)
    report.columns = list(df.columns)
    return df, report


def write(df: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".xlsx":
        df.to_excel(output, index=False)
    else:
        df.to_csv(output, index=False, encoding="utf-8")
