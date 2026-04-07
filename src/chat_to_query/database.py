from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # Centralized query execution keeps side effects easy to reason about.
    def execute_select(self, query: str) -> tuple[list[str], list[dict[str, Any]]]:
        with self.connect() as conn:
            cur = conn.execute(query)
            columns = [d[0] for d in cur.description or []]
            rows = [dict(r) for r in cur.fetchall()]
            return columns, rows

    def execute_many(self, query: str, rows: list[tuple[Any, ...]]) -> None:
        with self.connect() as conn:
            conn.executemany(query, rows)
            conn.commit()

    def execute(self, query: str) -> None:
        with self.connect() as conn:
            conn.execute(query)
            conn.commit()
