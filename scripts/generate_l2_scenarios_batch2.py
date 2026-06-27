"""Generate 4 additional L2 integration scenarios (batch 2, items 5-8)."""
import json
from pathlib import Path

ITEMS_DIR = Path(__file__).parent.parent / "test_items" / "l2"

SCENARIOS = [
    # ── Scenario 5: CLI Tool with Subcommands ──
    {
        "id": "L2-SCENARIO-005",
        "title": "Build a CLI Tool with Subcommands",
        "difficulty": 3,
        "tags": ["cli", "click", "tooling"],
        "prompt": (
            "# Task: Build a CLI Task Manager\n\n"
            "Create a Python CLI tool `tasker.py` using the `click` library with these subcommands:\n\n"
            "1. `tasker add <title>` — add a task with auto-generated UUID, status 'todo', "
            "created_at timestamp. Print the created task as JSON.\n"
            "2. `tasker list [--status todo|done|all]` — list tasks filtered by status (default: all), "
            "formatted as a table\n"
            "3. `tasker done <task_id>` — mark a task as done. Print error if task_id not found.\n"
            "4. `tasker delete <task_id>` — delete a task. Print confirmation.\n"
            "5. Tasks are persisted to `tasks.json` in the current directory.\n\n"
            "Deliverables: `tasker.py` (standalone, runnable with `python tasker.py`), "
            "`test_tasker.py` with at least 5 test cases."
        ),
        "files": {
            "tasker.py": (
                '"""Task Manager CLI — implement the subcommands below."""\n'
                'import click\n\n'
                '@click.group()\n'
                'def cli():\n'
                '    """A simple task manager."""\n'
                '    pass\n\n'
                '@cli.command()\n'
                '@click.argument("title")\n'
                'def add(title):\n'
                '    """Add a new task."""\n'
                '    # TODO: implement\n'
                '    pass\n\n'
                'if __name__ == "__main__":\n'
                '    cli()\n'
            ),
            "requirements.txt": "click>=8.1.0\n",
            "README.md": "# Tasker CLI\n\nImplement the task manager per the requirements.\n",
        },
        "expected_artifacts": ["tasker.py", "test_tasker.py"],
    },
    # ── Scenario 6: Web Scraper with Caching ──
    {
        "id": "L2-SCENARIO-006",
        "title": "Build a Web Scraper with Local Caching",
        "difficulty": 4,
        "tags": ["scraping", "cache", "requests"],
        "prompt": (
            "# Task: Build a Web Scraper with Caching\n\n"
            "Create `scraper.py` that:\n\n"
            "1. Accepts a URL as CLI argument\n"
            "2. Fetches the page HTML (using `requests` or `httpx`)\n"
            "3. Extracts all `<a href=\"...\">` links and their text\n"
            "4. Caches results to `.scraper_cache/{hash}.json` — if the same URL "
            "is requested within 1 hour, return cached data instead of re-fetching\n"
            "5. Implements exponential backoff retry (3 attempts, 1s/2s/4s delays) "
            "on connection errors\n"
            "6. Respects robots.txt (skip URL if Disallowed)\n"
            "7. Outputs results as JSON: {\"url\":\"...\", \"links\": [{\"href\":\"...\", \"text\":\"...\"}], \"cached\": bool, \"fetched_at\": \"...\"}\n\n"
            "Deliverables: `scraper.py`, `test_scraper.py`."
        ),
        "files": {
            "scraper.py": (
                '"""Web scraper with caching — implement per requirements."""\n'
                'import sys\n\n'
                'def scrape(url: str) -> dict:\n'
                '    # TODO: implement\n'
                '    pass\n\n'
                'if __name__ == "__main__":\n'
                '    if len(sys.argv) < 2:\n'
                '        print("Usage: python scraper.py <url>")\n'
                '        sys.exit(1)\n'
                '    result = scrape(sys.argv[1])\n'
                '    import json\n'
                '    print(json.dumps(result, indent=2))\n'
            ),
            "requirements.txt": "requests>=2.31.0\nhttpx>=0.27.0\n",
            "README.md": "# Web Scraper\n\nImplement with caching and retry logic.\n",
        },
        "expected_artifacts": ["scraper.py", "test_scraper.py"],
    },
    # ── Scenario 7: Database Migration Manager ──
    {
        "id": "L2-SCENARIO-007",
        "title": "Implement a Database Migration Manager",
        "difficulty": 4,
        "tags": ["database", "migration", "sqlite"],
        "prompt": (
            "# Task: Database Migration Manager\n\n"
            "In the provided project, implement `migrate.py` — a simple database "
            "migration tool:\n\n"
            "1. Reads migration SQL files from `migrations/` directory, sorted by "
            "filename (format: `001_desc.sql`, `002_desc.sql`, etc.)\n"
            "2. Tracks which migrations have been applied in a `_migrations` table "
            "(auto-created if missing)\n"
            "3. `--up` applies all pending migrations in order, each wrapped in a "
            "transaction\n"
            "4. `--down` rolls back the last applied migration batch\n"
            "5. `--status` prints which migrations are applied vs pending\n"
            "6. Uses SQLite (via sqlite3 standard library)\n\n"
            "Deliverables: `migrate.py`, `test_migrate.py`."
        ),
        "files": {
            "migrate.py": (
                '"""Database migration manager."""\n'
                'import sqlite3\n'
                'import os\n'
                'from pathlib import Path\n\n'
                'MIGRATIONS_DIR = Path("migrations")\n\n'
                'def init_db(conn):\n'
                '    conn.execute("CREATE TABLE IF NOT EXISTS _migrations (filename TEXT PRIMARY KEY, applied_at TEXT)")\n\n'
                'def get_applied(conn):\n'
                '    return {row[0] for row in conn.execute("SELECT filename FROM _migrations").fetchall()}\n\n'
                'def migrate_up(db_path: str = "app.db") -> list[str]:\n'
                '    """Apply pending migrations. Returns list of applied filenames."""\n'
                '    # TODO: implement\n'
                '    pass\n\n'
                'def migrate_down(db_path: str = "app.db") -> list[str]:\n'
                '    """Rollback last migration. Returns list of rolled-back filenames."""\n'
                '    # TODO: implement\n'
                '    pass\n\n'
                'def show_status(db_path: str = "app.db"):\n'
                '    """Print migration status."""\n'
                '    # TODO: implement\n'
                '    pass\n\n'
                'if __name__ == "__main__":\n'
                '    import sys\n'
                '    if "--up" in sys.argv:\n'
                '        migrate_up()\n'
                '    elif "--down" in sys.argv:\n'
                '        migrate_down()\n'
                '    elif "--status" in sys.argv:\n'
                '        show_status()\n'
            ),
            "migrations/001_create_users.sql": (
                "CREATE TABLE IF NOT EXISTS users (\n"
                "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                "    name TEXT NOT NULL,\n"
                "    email TEXT UNIQUE NOT NULL\n"
                ");\n"
            ),
            "migrations/002_add_profiles.sql": (
                "CREATE TABLE IF NOT EXISTS profiles (\n"
                "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                "    user_id INTEGER REFERENCES users(id),\n"
                "    bio TEXT,\n"
                "    avatar_url TEXT\n"
                ");\n"
            ),
            "README.md": "# Migration Manager\n\nImplement per requirements.\n",
        },
        "expected_artifacts": ["migrate.py", "test_migrate.py"],
    },
    # ── Scenario 8: API Rate Limiter ──
    {
        "id": "L2-SCENARIO-008",
        "title": "Implement a Token Bucket Rate Limiter",
        "difficulty": 3,
        "tags": ["api", "rate-limit", "middleware"],
        "prompt": (
            "# Task: Token Bucket Rate Limiter\n\n"
            "Implement `rate_limiter.py` that provides a token bucket rate limiter:\n\n"
            "1. `RateLimiter(capacity: int, refill_rate: float)` — capacity is max tokens, "
            "refill_rate is tokens per second\n"
            "2. `allow(key: str) -> bool` — return True if request allowed, False if "
            "rate limited. Each call consumes 1 token.\n"
            "3. Tokens refill gradually based on elapsed time since last refill\n"
            "4. Implement `RateLimitMiddleware` as a Flask middleware that:\n"
            "   - Limits per IP address (use `request.remote_addr`)\n"
            "   - Returns 429 with `{\"error\":\"rate_limited\",\"retry_after\":X}` when limited\n"
            "   - Adds `X-RateLimit-Remaining` and `X-RateLimit-Limit` headers\n"
            "5. Must be thread-safe (use `threading.Lock`)\n\n"
            "Deliverables: `rate_limiter.py`, `test_rate_limiter.py`."
        ),
        "files": {
            "rate_limiter.py": (
                '"""Token bucket rate limiter — implement per requirements."""\n'
                'import time\n'
                'import threading\n\n'
                'class RateLimiter:\n'
                '    def __init__(self, capacity: int, refill_rate: float):\n'
                '        """capacity: max tokens, refill_rate: tokens/second"""\n'
                '        pass\n\n'
                '    def allow(self, key: str) -> bool:\n'
                '        """Return True if request is allowed."""\n'
                '        pass\n\n'
                'class RateLimitMiddleware:\n'
                '    """Flask WSGI middleware for per-IP rate limiting."""\n'
                '    def __init__(self, app, capacity: int = 60, refill_rate: float = 1.0):\n'
                '        pass\n\n'
                '    def __call__(self, environ, start_response):\n'
                '        pass\n'
            ),
            "requirements.txt": "flask>=3.0.0\n",
            "README.md": "# Token Bucket Rate Limiter\n\nImplement a thread-safe token bucket.\n",
        },
        "expected_artifacts": ["rate_limiter.py", "test_rate_limiter.py"],
    },
]


def main():
    for s in SCENARIOS:
        item_dir = ITEMS_DIR / s["id"]
        context_dir = item_dir / "context"
        judge_dir = item_dir / "judge"
        context_dir.mkdir(parents=True, exist_ok=True)
        judge_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in s["files"].items():
            fp = context_dir / filename
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content)

        metadata = {
            "id": s["id"],
            "layer": "L2",
            "dimensions": ["D1", "D2", "D3", "D5"],
            "sub_dimensions": ["D4", "D6"],
            "language": "python",
            "difficulty": s["difficulty"],
            "estimated_time_min": 45,
            "tags": s["tags"],
            "sandbox": {
                "image": "python",
                "dependencies": ["pytest", "flask", "click", "requests"],
                "network": "whitelist",
            },
            "prompt_template": s["prompt"],
            "context_files": [str(Path("context") / f) for f in s["files"].keys()],
            "expected_artifacts": s["expected_artifacts"],
            "scoring": {"type": "llm_judge", "pass_threshold": 0.70},
            "created": "2026-07-10",
            "version": "1.0",
        }
        (item_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False)
        )
        print(f"Created {s['id']}: {s['title']}")

    # Update registry
    with open(ITEMS_DIR.parent / "registry.json") as f:
        reg = json.load(f)
    for s in SCENARIOS:
        entry = {"id": s["id"], "path": f"l2/{s['id']}", "enabled": True}
        if entry not in reg["items"]:
            reg["items"].append(entry)
    with open(ITEMS_DIR.parent / "registry.json", "w") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
    print(f"Registry updated: {len(reg['items'])} items total")


if __name__ == "__main__":
    main()
