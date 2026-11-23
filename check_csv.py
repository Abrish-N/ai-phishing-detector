import csv
from pathlib import Path
import sys

csv.field_size_limit(sys.maxsize)

expected_columns = [
    "id",
    "subject",
    "sender",
    "body",
    "contains_link",
    "urgent_word",
    "suspicious_sender",
    "label",
]
p = Path("emails.csv")
with p.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f)
    header = next(reader, [])
    if header != expected_columns:
        raise ValueError(f"Expected CSV header {expected_columns}, got {header}")

    malformed_rows = [
        (line_number, len(row))
        for line_number, row in enumerate(reader, start=2)
        if len(row) != len(expected_columns)
    ]

if malformed_rows:
    for line_number, column_count in malformed_rows:
        print(f"Row {line_number}: expected {len(expected_columns)} columns, got {column_count}")
else:
    print(f"{p} has the expected header and all rows have {len(expected_columns)} columns.")
