"""Database migration manager."""
import sqlite3
import os
from pathlib import Path

MIGRATIONS_DIR = Path("migrations")

def init_db(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS _migrations (filename TEXT PRIMARY KEY, applied_at TEXT)")

def get_applied(conn):
    return {row[0] for row in conn.execute("SELECT filename FROM _migrations").fetchall()}

def migrate_up(db_path: str = "app.db") -> list[str]:
    """Apply pending migrations. Returns list of applied filenames."""
    # TODO: implement
    pass

def migrate_down(db_path: str = "app.db") -> list[str]:
    """Rollback last migration. Returns list of rolled-back filenames."""
    # TODO: implement
    pass

def show_status(db_path: str = "app.db"):
    """Print migration status."""
    # TODO: implement
    pass

if __name__ == "__main__":
    import sys
    if "--up" in sys.argv:
        migrate_up()
    elif "--down" in sys.argv:
        migrate_down()
    elif "--status" in sys.argv:
        show_status()
