from pathlib import Path

import pandas as pd

from csv_cleaner.core import clean, dedupe_headers, normalize_header

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def test_normalize_header():
    assert normalize_header("  Customer Name ") == "customer_name"
    assert normalize_header("E-mail") == "e_mail"
    assert normalize_header("   ") == "column"


def test_dedupe_headers():
    assert dedupe_headers(["a", "b", "a", "a"]) == ["a", "b", "a_1", "a_2"]


def test_clean_samples_merges_and_dedupes():
    df, report = clean([SAMPLES], date_columns=["order date"], dayfirst=True, dedupe_on=["order id"])
    assert report.files == ["orders_extra.csv", "orders_september.csv"]
    assert report.rows_in == 8
    assert report.empty_rows_removed == 1
    assert report.duplicates_removed == 2  # 1002 repeated, 1003 in both files
    assert sorted(df["order_id"]) == ["1001", "1002", "1003", "1004", "1005"]


def test_text_and_dates_are_cleaned():
    df, _ = clean([SAMPLES], date_columns=["order date"], dayfirst=True, dedupe_on=["order id"])
    row = df.set_index("order_id").loc["1001"]
    assert row["customer_name"] == "Ana Pérez"
    assert row["order_date"] == "2026-09-03"
    assert df.set_index("order_id").loc["1004", "customer_name"] == "María Gómez"


def test_output_xlsx(tmp_path):
    from csv_cleaner.core import write

    df, _ = clean([SAMPLES])
    out = tmp_path / "out.xlsx"
    write(df, out)
    assert len(pd.read_excel(out)) == len(df)


def test_iso_dates_ignore_dayfirst():
    df, _ = clean([SAMPLES], date_columns=["order date"], dayfirst=True, dedupe_on=["order id"])
    assert df.set_index("order_id").loc["1004", "order_date"] == "2026-09-12"
