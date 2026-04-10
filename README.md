# Chat_To_Query

Read-only SQL assistant with SQLite + OpenAI API.

System Review Video:

[![Chat To Query](http://img.youtube.com/vi/gIeVEGgdGoY/0.jpg)](http://www.youtube.com/watch?v=gIeVEGgdGoY "Chat To Query")

## Features
- Load CSV into SQLite
- Ask natural-language questions
- Generate SQL with OpenAI
- Validate SQL before execution (SELECT-only)

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables:
```bash
export OPENAI_API_KEY="your_key"
export OPENAI_MODEL="gpt-4o-mini"
export DB_PATH="data/app.db"
```

## Run
```bash
PYTHONPATH=src python -m chat_to_query
```

## Commands
- `:help`
- `:tables`
- `:schema <table>`
- `:load <csv_path> [table_name]`
- `:sql <SELECT ...>`
- `:quit`

## Test
```bash
PYTHONPATH=src pytest -q
```
