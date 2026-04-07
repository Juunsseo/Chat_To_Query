from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .database import Database
from .llm_adapter import LLMAdapter
from .schema_manager import SchemaManager
from .validator import QueryValidator


@dataclass(frozen=True)
class QueryResponse:
    sql: str
    columns: list[str]
    rows: list[dict[str, Any]]


class QueryService:
    def __init__(
        self,
        db: Database,
        schema_manager: SchemaManager,
        validator: QueryValidator,
        llm_adapter: LLMAdapter,
    ) -> None:
        self.db = db
        self.schema_manager = schema_manager
        self.validator = validator
        self.llm_adapter = llm_adapter

    def ask(self, question: str) -> QueryResponse:
        schema = self.schema_manager.schema_prompt_context()
        sql = self.llm_adapter.generate_sql(question, schema)

        validation = self.validator.validate_select(sql)
        if not validation.is_valid:
            raise ValueError(f"Rejected SQL: {validation.reason}\nSQL: {sql}")

        columns, rows = self.db.execute_select(validation.normalized_query)
        return QueryResponse(sql=validation.normalized_query, columns=columns, rows=rows)

    def run_sql(self, sql: str) -> QueryResponse:
        validation = self.validator.validate_select(sql)
        if not validation.is_valid:
            raise ValueError(f"Rejected SQL: {validation.reason}")

        columns, rows = self.db.execute_select(validation.normalized_query)
        return QueryResponse(sql=validation.normalized_query, columns=columns, rows=rows)
