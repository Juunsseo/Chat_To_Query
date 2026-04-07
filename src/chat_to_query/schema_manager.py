from __future__ import annotations

import re
from dataclasses import dataclass

from .database import Database


@dataclass(frozen=True)
class TableSchema:
    table_name: str
    columns: dict[str, str]


class SchemaManager:
    def __init__(self, db: Database) -> None:
        self.db = db

    def list_tables(self) -> list[str]:
        sql = (
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        _, rows = self.db.execute_select(sql)
        return [r["name"] for r in rows]

    def get_table_schema(self, table_name: str) -> TableSchema:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
            raise ValueError(f"Invalid table name: {table_name}")

        sql = f"PRAGMA table_info({table_name})"
        _, rows = self.db.execute_select(sql)
        if not rows:
            raise ValueError(f"Table not found: {table_name}")

        columns: dict[str, str] = {}
        for r in rows:
            columns[r["name"]] = (r["type"] or "TEXT").upper()

        return TableSchema(table_name=table_name, columns=columns)

    # Provide compact schema text to guide the model.
    def schema_prompt_context(self) -> str:
        tables = self.list_tables()
        if not tables:
            return "No tables found."

        lines: list[str] = []
        for table in tables:
            schema = self.get_table_schema(table)
            col_line = ", ".join(f"{k} {v}" for k, v in schema.columns.items())
            lines.append(f"{schema.table_name}({col_line})")
        return "\n".join(lines)
