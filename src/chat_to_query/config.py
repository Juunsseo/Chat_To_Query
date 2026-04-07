from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_path: str
    openai_api_key: str
    openai_model: str


# Keep config in one place so modules stay simple.
def load_settings() -> Settings:
    return Settings(
        db_path=os.getenv("DB_PATH", "data/app.db"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )
