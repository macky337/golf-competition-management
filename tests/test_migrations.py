import importlib.util
from pathlib import Path
import sys

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "manage_migrations.py"
SPEC = importlib.util.spec_from_file_location("manage_migrations", MODULE_PATH)
assert SPEC and SPEC.loader, "manage_migrations.py not found"
manage_migrations = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = manage_migrations
SPEC.loader.exec_module(manage_migrations)  # type: ignore[arg-type]

load_migration_files = manage_migrations.load_migration_files
resolve_database_url = manage_migrations.resolve_database_url


def test_load_migration_files_are_sorted():
    files = load_migration_files(Path("migrations"))
    names = [migration.name for migration in files]
    assert names == sorted(names)
    # Migration files should not be empty
    for migration in files:
        sql = migration.read_sql().strip()
        assert sql, f"{migration.name} is empty"


def test_resolve_database_url_prefers_direct_argument(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    override_value = "postgresql://user:pass@localhost:5432/db"
    result = resolve_database_url(override_value)
    assert result == override_value


def test_resolve_database_url_from_environment(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    expected = "postgresql://env:pass@localhost:5432/db"
    monkeypatch.setenv("SUPABASE_DB_URL", expected)
    result = resolve_database_url(None)
    assert result == expected
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)


def test_resolve_database_url_none_when_missing(monkeypatch):
    for key in [
        "DATABASE_URL",
        "SUPABASE_DB_URL",
        "SUPABASE_POSTGRES_URL",
        "SUPABASE_CONNECTION_STRING",
    ]:
        monkeypatch.delenv(key, raising=False)
    assert resolve_database_url(None) is None
