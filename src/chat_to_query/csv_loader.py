from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable

from .database import Database


class CSVLoader:
    def __init__(self, db: Database) -> None:
        self.db = db

    def load_csv(self, csv_path: str, table_name: str | None = None) -> str:
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV must include header row")

            raw_columns = [c.strip() for c in reader.fieldnames]
            columns = [self._normalize_identifier(c) for c in raw_columns]
            if len(set(columns)) != len(columns):
                raise ValueError("CSV contains duplicate column names after normalization")

            table = table_name or path.stem
            table = self._normalize_identifier(table)
            rows = list(reader)

        types = self._infer_types(rows, raw_columns)
        create_sql = self._build_create_table_sql(table, columns, types)
        self.db.execute(create_sql)

        placeholders = ", ".join(["?" for _ in columns])
        insert_sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        params = [tuple(row.get(c, "") for c in raw_columns) for row in rows]
        self.db.execute_many(insert_sql, params)
        return table

    # Keep names SQL-safe and predictable.
    def _normalize_identifier(self, s: str) -> str:
        s = s.strip().lower()
        s = re.sub(r"[^a-z0-9_]+", "_", s)
        s = re.sub(r"_+", "_", s).strip("_")
        if not s:
            raise ValueError("Invalid identifier")
        if s[0].isdigit():
            s = f"c_{s}"
        return s

    def _infer_types(self, rows: list[dict[str, str]], raw_columns: list[str]) -> list[str]:
        inferred: list[str] = []
        for col in raw_columns:
            values = [r.get(col, "").strip() for r in rows if (r.get(col, "") or "").strip()]
            inferred.append(self._infer_one(values))
        return inferred

    def _infer_one(self, values: Iterable[str]) -> str:
        has_values = False
        int_ok = True
        float_ok = True
        for v in values:
            has_values = True
            if int_ok:
                try:
                    int(v)
                except ValueError:
                    int_ok = False
            if float_ok:
                try:
                    float(v)
                except ValueError:
                    float_ok = False

        if not has_values:
            return "TEXT"
        if int_ok:
            return "INTEGER"
        if float_ok:
            return "REAL"
        return "TEXT"

    def _build_create_table_sql(self, table: str, columns: list[str], types: list[str]) -> str:
        col_defs = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
        for c, t in zip(columns, types, strict=True):
            col_defs.append(f"{c} {t}")
        return f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(col_defs)})"
