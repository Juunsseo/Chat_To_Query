from __future__ import annotations

import argparse
import json

from .config import load_settings
from .csv_loader import CSVLoader
from .database import Database
from .llm_adapter import LLMAdapter
from .query_service import QueryService
from .schema_manager import SchemaManager
from .validator import QueryValidator


def build_services() -> tuple[CSVLoader, SchemaManager, QueryService]:
    settings = load_settings()
    db = Database(settings.db_path)
    schema = SchemaManager(db)
    validator = QueryValidator(schema)
    llm = LLMAdapter(api_key=settings.openai_api_key, model=settings.openai_model)
    service = QueryService(db=db, schema_manager=schema, validator=validator, llm_adapter=llm)
    loader = CSVLoader(db)
    return loader, schema, service


def _print_rows(columns: list[str], rows: list[dict[str, object]], limit: int = 20) -> None:
    print(f"rows={len(rows)}")
    if not rows:
        return
    shown = rows[:limit]
    print(json.dumps({"columns": columns, "rows": shown}, indent=2, ensure_ascii=False))
    if len(rows) > limit:
        print(f"... truncated {len(rows) - limit} rows")


def run_interactive() -> None:
    loader, schema, service = build_services()

    print("Read-only SQL assistant ready.")
    print("Commands: :help, :tables, :schema <table>, :load <csv> [table], :sql <SELECT>, :quit")

    while True:
        text = input("\n> ").strip()
        if not text:
            continue

        if text in {":quit", ":exit"}:
            print("bye")
            return

        if text == ":help":
            print("Type a natural-language question, or use commands above.")
            continue

        if text == ":tables":
            print("\n".join(schema.list_tables()) or "(no tables)")
            continue

        if text.startswith(":schema "):
            table = text.split(maxsplit=1)[1].strip()
            try:
                s = schema.get_table_schema(table)
                for name, typ in s.columns.items():
                    print(f"{name}: {typ}")
            except Exception as e:
                print(f"error: {e}")
            continue

        if text.startswith(":load "):
            parts = text.split()
            if len(parts) < 2:
                print("usage: :load <csv_path> [table_name]")
                continue
            csv_path = parts[1]
            table_name = parts[2] if len(parts) > 2 else None
            try:
                table = loader.load_csv(csv_path, table_name)
                print(f"loaded into table: {table}")
            except Exception as e:
                print(f"error: {e}")
            continue

        if text.startswith(":sql "):
            sql = text.split(maxsplit=1)[1]
            try:
                result = service.run_sql(sql)
                print(f"SQL: {result.sql}")
                _print_rows(result.columns, result.rows)
            except Exception as e:
                print(f"error: {e}")
            continue

        try:
            # Default behavior: NL question -> LLM -> validated SQL -> read-only execution.
            result = service.ask(text)
            print(f"SQL: {result.sql}")
            _print_rows(result.columns, result.rows)
        except Exception as e:
            print(f"error: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only SQL assistant")
    parser.add_argument("--once", help="Ask one question and exit")
    parser.add_argument("--sql", help="Run one SELECT and exit")
    args = parser.parse_args()

    _, _, service = build_services()

    if args.sql:
        result = service.run_sql(args.sql)
        print(f"SQL: {result.sql}")
        _print_rows(result.columns, result.rows)
        return

    if args.once:
        result = service.ask(args.once)
        print(f"SQL: {result.sql}")
        _print_rows(result.columns, result.rows)
        return

    run_interactive()


if __name__ == "__main__":
    main()
