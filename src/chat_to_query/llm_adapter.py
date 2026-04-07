from __future__ import annotations

import re

from openai import OpenAI


class LLMAdapter:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    # Keep prompt strict so the validator has less noisy SQL to clean up.
    def generate_sql(self, question: str, schema_context: str) -> str:
        prompt = f"""
You convert natural language into a single SQLite SELECT query.
Rules:
- Return ONLY SQL, no markdown, no explanation.
- Use only tables/columns from the schema.
- Generate exactly one SELECT statement.
- No INSERT/UPDATE/DELETE/DDL.

Schema:
{schema_context}

User question:
{question}
""".strip()

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=0,
        )

        sql = (response.output_text or "").strip()
        sql = self._strip_code_fences(sql)
        return sql

    def _strip_code_fences(self, text: str) -> str:
        # Recover SQL if model wrapped output in ```sql blocks.
        m = re.search(r"```(?:sql)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1).strip()
        return text
