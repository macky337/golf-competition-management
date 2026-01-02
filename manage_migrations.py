#!/usr/bin/env python3
"""Simple migration runner for PostgreSQL-compatible databases.

Usage examples:
    python manage_migrations.py --dry-run
    python manage_migrations.py --database-url=$DATABASE_URL
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Set

from dotenv import load_dotenv

try:
    import psycopg
except ModuleNotFoundError as exc:  # pragma: no cover - guarded by requirements
    raise SystemExit(
        "psycopg is required to run migrations. Install dependencies via `pip install -r requirements.txt`."
    ) from exc


@dataclass(frozen=True)
class MigrationFile:
    """Represents a single SQL migration file."""

    name: str
    path: Path

    def read_sql(self) -> str:
        return self.path.read_text(encoding="utf-8")


def load_migration_files(directory: Path) -> List[MigrationFile]:
    """Return migration files sorted lexicographically."""

    if not directory.exists():
        raise FileNotFoundError(f"Migration directory not found: {directory}")

    files = [
        MigrationFile(name=path.name, path=path)
        for path in sorted(directory.glob("*.sql"))
        if path.is_file()
    ]
    if not files:
        raise FileNotFoundError(f"No .sql files found in {directory}")
    return files


def ensure_schema_table(connection: psycopg.Connection) -> None:
    """Create schema_migrations table if necessary."""

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            filename TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
        );
        """
    )
    connection.commit()


def fetch_applied_migrations(connection: psycopg.Connection) -> Set[str]:
    """Return set of already-applied migration filenames."""

    ensure_schema_table(connection)
    rows = connection.execute("SELECT filename FROM schema_migrations ORDER BY filename").fetchall()
    return {row[0] for row in rows}


def apply_pending_migrations(
    connection: psycopg.Connection,
    files: Sequence[MigrationFile],
    dry_run: bool = False,
) -> int:
    """Apply migrations sequentially. Returns number of applied migrations."""

    applied = fetch_applied_migrations(connection)
    to_apply = [migration for migration in files if migration.name not in applied]

    if not to_apply:
        print("✅ No new migrations to apply.")
        return 0

    print(f"Found {len(to_apply)} pending migration(s).")
    if dry_run:
        for migration in to_apply:
            print(f"- {migration.name} (pending)")
        print("Dry-run complete. No changes were written.")
        return 0

    for migration in to_apply:
        sql = migration.read_sql()
        print(f"Applying {migration.name} ...", end=" ")
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cursor.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)",
                (migration.name,),
            )
        connection.commit()
        print("done")

    return len(to_apply)


def list_migrations(files: Sequence[MigrationFile], applied: Iterable[str]) -> None:
    applied_set = set(applied)
    for migration in files:
        status = "applied" if migration.name in applied_set else "pending"
        print(f"{migration.name}: {status}")


def resolve_database_url(cli_value: str | None) -> str | None:
    if cli_value:
        return cli_value
    load_dotenv()
    env_keys = [
        "DATABASE_URL",
        "SUPABASE_DB_URL",
        "SUPABASE_POSTGRES_URL",
        "SUPABASE_CONNECTION_STRING",
    ]
    for key in env_keys:
        value = os.getenv(key)
        if value:
            return value
    return None


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple SQL migration runner")
    parser.add_argument(
        "--database-url",
        dest="database_url",
        help="PostgreSQL connection string. Defaults to DATABASE_URL or Supabase env vars.",
    )
    parser.add_argument(
        "--migrations-dir",
        default="migrations",
        help="Directory containing .sql migration files (default: migrations)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List pending migrations without touching the database.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List migration status and exit.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if no database URL is available, even for dry-run mode.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    migrations_dir = Path(args.migrations_dir)
    files = load_migration_files(migrations_dir)

    database_url = resolve_database_url(args.database_url)

    if not database_url:
        if args.dry_run and not args.strict:
            print("No database URL detected. Displaying migration plan only.\n")
            for migration in files:
                print(f"- {migration.name}")
            return 0
        raise SystemExit(
            "Database URL not provided. Set DATABASE_URL (or Supabase *_DB_URL) or pass --database-url."
        )

    with psycopg.connect(database_url) as connection:
        if args.list:
            applied = fetch_applied_migrations(connection)
            list_migrations(files, applied)
            return 0
        applied_count = apply_pending_migrations(connection, files, dry_run=args.dry_run)

    if applied_count:
        print(f"Applied {applied_count} migration(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
