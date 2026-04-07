from chat_to_query.database import Database
from chat_to_query.schema_manager import SchemaManager
from chat_to_query.validator import QueryValidator


def _setup_db(tmp_path):
    db = Database(str(tmp_path / "t.db"))
    db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
    db.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, total REAL)")
    return db


def test_reject_non_select(tmp_path):
    db = _setup_db(tmp_path)
    validator = QueryValidator(SchemaManager(db))

    result = validator.validate_select("DELETE FROM users")
    assert not result.is_valid


def test_reject_unknown_table(tmp_path):
    db = _setup_db(tmp_path)
    validator = QueryValidator(SchemaManager(db))

    result = validator.validate_select("SELECT * FROM missing")
    assert not result.is_valid
    assert "Unknown table" in (result.reason or "")


def test_reject_unknown_column(tmp_path):
    db = _setup_db(tmp_path)
    validator = QueryValidator(SchemaManager(db))

    result = validator.validate_select("SELECT users.unknown FROM users")
    assert not result.is_valid


def test_allow_valid_select(tmp_path):
    db = _setup_db(tmp_path)
    validator = QueryValidator(SchemaManager(db))

    result = validator.validate_select("SELECT users.name FROM users")
    assert result.is_valid
