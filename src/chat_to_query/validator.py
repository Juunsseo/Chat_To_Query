from __future__ import annotations

import re
from dataclasses import dataclass

from .schema_manager import SchemaManager


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    normalized_query: str
    reason: str | None = None


class QueryValidator:
    FORBIDDEN = {
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "create",
        "replace",
        "pragma",
        "attach",
        "detach",
        "vacuum",
        "truncate",
    }

    def __init__(self, schema_manager: SchemaManager) -> None:
        self.schema_manager = schema_manager

    def validate_select(self, query: str) -> ValidationResult:
        q = query.strip()
        if not q:
            return ValidationResult(False, "", "Query is empty")

        # Strip one trailing semicolon for easier downstream handling.
        if q.endswith(";"):
            q = q[:-1].strip()

        lowered = q.lower()
        if not lowered.startswith("select"):
            return ValidationResult(False, q, "Only SELECT queries are allowed")

        if ";" in q or "--" in q or "/*" in q or "*/" in q:
            return ValidationResult(False, q, "Comments and multi-statements are not allowed")

        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", lowered)
        for t in tokens:
            if t in self.FORBIDDEN:
                return ValidationResult(False, q, f"Forbidden keyword: {t}")

        table_map = self._extract_table_aliases(q)
        if not table_map:
            return ValidationResult(False, q, "Query must include a FROM table")

        existing = set(self.schema_manager.list_tables())
        for table in table_map.values():
            if table not in existing:
                return ValidationResult(False, q, f"Unknown table: {table}")

        # Validate referenced columns against used tables.
        bad_column = self._find_unknown_column(q, table_map)
        if bad_column:
            return ValidationResult(False, q, bad_column)

        return ValidationResult(True, q)

    def _extract_table_aliases(self, query: str) -> dict[str, str]:
        # Capture FROM/JOIN targets and optional aliases.
        pattern = re.compile(
            r"\b(?:from|join)\s+([A-Za-z_][A-Za-z0-9_]*)"
            r"(?:\s+(?:as\s+)?([A-Za-z_][A-Za-z0-9_]*))?",
            flags=re.IGNORECASE,
        )
        table_map: dict[str, str] = {}
        for table, alias in pattern.findall(query):
            table_map[table] = table
            if alias:
                table_map[alias] = table
        return table_map

    def _find_unknown_column(self, query: str, alias_map: dict[str, str]) -> str | None:
        all_columns_by_table = {
            table: set(self.schema_manager.get_table_schema(table).columns.keys())
            for table in set(alias_map.values())
        }

        # Validate qualified refs like alias.column.
        for alias, column in re.findall(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b", query
        ):
            table = alias_map.get(alias)
            if not table:
                return f"Unknown table/alias: {alias}"
            if column not in all_columns_by_table[table]:
                return f"Unknown column: {alias}.{column}"

        return None
