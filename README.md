# csv-cleaner

Merge and clean messy CSV and Excel exports into one tidy file with a single command.

Built for the everyday mess of real business data: files from different systems,
different separators (`,` `;`), inconsistent headers, extra spaces, blank rows,
duplicated records and mixed date formats.

## What it does

| Problem | Fix |
|---|---|
| `Customer Name`, ` customer name `, `CUSTOMER-NAME` | Normalized to `customer_name` |
| `,` in one file and `;` in another | Separator detected automatically |
| `"  Ana   Pérez "` | Trimmed to `"Ana Pérez"` |
| Blank rows | Removed |
| Same order in two files | Removed (by all columns or by the key you choose) |
| `03/09/2026` and `2026-09-05` | Both converted to `YYYY-MM-DD` |
| Where did this row come from? | `source_file` column added |

## Example

Two messy exports in [`samples/`](samples):

```
orders_september.csv                         orders_extra.csv
Order ID,Customer Name, E-mail ,Order Date   order id;customer name;e-mail;order date
1001,  Ana Pérez ,ana@...,03/09/2026         1003;Li Wei;li@...;2026-09-05
1002,John   Smith,john@...,04/09/2026        1004;María  Gómez;maria@...;2026-09-12
,,,,                                         1005; Tom Baker ;tom@...;2026-09-20
1003,Li Wei,li@...,05/09/2026
1002,John   Smith,john@...,04/09/2026
```

```bash
python -m csv_cleaner samples --dates "order date" --dayfirst --dedupe-on "order id" -o cleaned.csv
```

```
Files merged:        2
Rows read:           8
Empty rows removed:  1
Duplicates removed:  2
Rows written:        5
Columns:             order_id, customer_name, e_mail, order_date, amount, source_file
Saved to:            cleaned.csv
```

`cleaned.csv`:

```
order_id,customer_name,e_mail,order_date,amount,source_file
1003,Li Wei,li@example.com,2026-09-05,45.00,orders_extra.csv
1004,María Gómez,maria@example.com,2026-09-12,230.00,orders_extra.csv
1005,Tom Baker,tom@example.com,2026-09-20,15.75,orders_extra.csv
1001,Ana Pérez,ana@example.com,2026-09-03,120.50,orders_september.csv
1002,John Smith,john@example.com,2026-09-04,89.90,orders_september.csv
```

## Install

Requires Python 3.9+.

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m csv_cleaner INPUTS... [-o OUTPUT] [--dates COL ...] [--dayfirst] [--dedupe-on COL ...] [--no-source]
```

- `INPUTS`: files or folders (`.csv`, `.xlsx`, `.xls`).
- `-o`: output file, `.csv` or `.xlsx` (default `cleaned.csv`).
- `--dates`: columns to convert to `YYYY-MM-DD`.
- `--dayfirst`: read `03/04/2026` as 3 April (ISO dates are never affected).
- `--dedupe-on`: columns that identify a duplicate, e.g. an order ID.
- `--no-source`: don't add the `source_file` column.

It can also be used from Python:

```python
from pathlib import Path
from csv_cleaner.core import clean, write

df, report = clean([Path("exports/")], date_columns=["order date"], dedupe_on=["order id"])
print(report.summary())
write(df, Path("cleaned.xlsx"))
```

## Tests

```bash
pip install pytest
pytest
```

## Need something similar?

I build data-cleaning scripts, Excel / Google Sheets automations and dashboards.
Contact me on [Fiverr](https://www.fiverr.com/juangiles260).

## License

MIT
