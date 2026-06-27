"""Generate 2 L3 long-running projects — memory and multi-agent oriented."""
import json
from pathlib import Path

ITEMS_DIR = Path(__file__).parent.parent / "test_items" / "l3"

# ── Project 1: Cross-session Feature Iteration (Memory-focused) ──
P1_SESSIONS = [
    {
        "session": 1,
        "title": "Session 1: Build the Core API",
        "prompt": (
            "# Project: Mini E-Commerce API — Session 1 of 3\n\n"
            "Build the foundation of a mini e-commerce REST API using Flask:\n\n"
            "1. Create `app.py` with Flask app\n"
            "2. Implement `POST /products` — create a product with {name, price, stock}\n"
            "3. Implement `GET /products` — list all products\n"
            "4. Implement `GET /products/<id>` — get single product\n"
            "5. Store products in an in-memory list (will be upgraded to DB in session 2)\n"
            "6. Add input validation: name required, price > 0, stock >= 0\n"
            "7. Write `test_app.py` with pytest tests for all endpoints\n"
            "8. Create `DESIGN.md` documenting your API design decisions\n\n"
            "KEY: Remember your design choices — in session 2 you will add user auth "
            "and switch to a database. Your DESIGN.md will help you maintain context."
        ),
    },
    {
        "session": 2,
        "title": "Session 2: Add Auth + Database",
        "prompt": (
            "# Project: Mini E-Commerce API — Session 2 of 3\n\n"
            "Continue from where you left off. The project should have:\n"
            "- Flask app with product CRUD endpoints (in-memory)\n"
            "- `test_app.py` with tests\n"
            "- `DESIGN.md` with your design notes\n\n"
            "NEW tasks:\n"
            "1. Add JWT authentication middleware — protect all `/products` routes\n"
            "2. Create `POST /auth/register` and `POST /auth/login` endpoints\n"
            "3. Switch from in-memory storage to SQLite using SQLAlchemy\n"
            "4. Create a `models.py` with User and Product models\n"
            "5. Update `DESIGN.md` with auth and database design decisions\n"
            "6. Update all tests — they must still pass\n"
            "7. Add `requirements.txt` with flask, sqlalchemy, pyjwt\n\n"
            "The test from session 1 should still work after your changes — "
            "this verifies you maintained backward compatibility."
        ),
    },
    {
        "session": 3,
        "title": "Session 3: Orders + Reporting",
        "prompt": (
            "# Project: Mini E-Commerce API — Session 3 of 3\n\n"
            "Continue from sessions 1-2. The project should have:\n"
            "- JWT auth with user registration/login\n"
            "- SQLite database with User and Product models\n"
            "- Product CRUD endpoints (protected)\n"
            "- Updated tests and DESIGN.md\n\n"
            "NEW tasks:\n"
            "1. Create `POST /orders` — authenticated user places an order "
            "(validate products exist and have sufficient stock)\n"
            "2. Create `GET /orders` — list current user's orders\n"
            "3. Create `GET /orders/<id>` — get order detail (only owner or admin)\n"
            "4. Add `GET /report/products` — report endpoint showing total sales per product\n"
            "5. Add `GET /report/revenue` — total revenue, total orders, average order value\n"
            "6. Update `DESIGN.md` with final architecture notes\n"
            "7. Ensure all existing tests still pass + add new tests for orders and reports\n\n"
            "FINAL: Your DESIGN.md should now document the complete architecture "
            "across all 3 sessions. This tests whether you maintained context."
        ),
    },
]

# ── Project 2: Multi-Agent Large Refactor (Collaboration-focused) ──
P2_SESSIONS = [
    {
        "session": 1,
        "title": "Session 1: Analyze & Plan the Refactor",
        "prompt": (
            "# Project: Library Management System Refactor — Session 1 of 2\n\n"
            "You are given a monolithic `library.py` (800 lines) that handles "
            "books, members, loans, fines, and reporting all in one file with "
            "tightly coupled classes.\n\n"
            "Your tasks:\n"
            "1. Read and fully understand `library.py`\n"
            "2. Write `REFACTOR_PLAN.md` documenting:\n"
            "   - The current architecture and its problems\n"
            "   - Proposed new modular structure (which sub-agents should handle what)\n"
            "   - Migration strategy (incremental, keep tests passing)\n"
            "3. Create `test_library.py` with integration tests covering the current "
            "behavior (these tests act as a safety net for the refactor)\n"
            "4. Identify which parts are independent and can be extracted in parallel\n\n"
            "IMPORTANT: In session 2, you MUST use sub-agents to perform the actual "
            "refactor. Use the Task/Agent dispatching mechanism to assign each module "
            "to a separate sub-agent. Plan accordingly now."
        ),
        "files": {
            "library.py": (
                '"""Monolithic Library Management System — needs refactoring."""\n'
                'from dataclasses import dataclass, field\n'
                'from typing import Optional\n'
                'from datetime import datetime, timedelta\n\n\n'
                '@dataclass\n'
                'class Book:\n'
                '    id: int\n'
                '    title: str\n'
                '    author: str\n'
                '    isbn: str\n'
                '    available: bool = True\n\n\n'
                '@dataclass\n'
                'class Member:\n'
                '    id: int\n'
                '    name: str\n'
                '    email: str\n'
                '    joined: str\n'
                '    active: bool = True\n'
                '    fines_due: float = 0.0\n\n\n'
                '@dataclass\n'
                'class Loan:\n'
                '    id: int\n'
                '    book_id: int\n'
                '    member_id: int\n'
                '    borrowed: str\n'
                '    due: str\n'
                '    returned: Optional[str] = None\n\n\n'
                'class Library:\n'
                '    """Monolithic class handling everything."""\n\n'
                '    def __init__(self):\n'
                '        self.books: list[Book] = []\n'
                '        self.members: list[Member] = []\n'
                '        self.loans: list[Loan] = []\n'
                '        self._next_book_id = 1\n'
                '        self._next_member_id = 1\n'
                '        self._next_loan_id = 1\n\n'
                '    # ── Book operations ──\n'
                '    def add_book(self, title: str, author: str, isbn: str) -> Book:\n'
                '        b = Book(id=self._next_book_id, title=title, author=author, isbn=isbn)\n'
                '        self._next_book_id += 1\n'
                '        self.books.append(b)\n'
                '        return b\n\n'
                '    def find_book(self, book_id: int) -> Optional[Book]:\n'
                '        for b in self.books:\n'
                '            if b.id == book_id:\n'
                '                return b\n'
                '        return None\n\n'
                '    def search_books(self, query: str) -> list[Book]:\n'
                '        q = query.lower()\n'
                '        return [b for b in self.books if q in b.title.lower() or q in b.author.lower()]\n\n'
                '    def list_available_books(self) -> list[Book]:\n'
                '        return [b for b in self.books if b.available]\n\n'
                '    # ── Member operations ──\n'
                '    def register_member(self, name: str, email: str) -> Member:\n'
                '        m = Member(id=self._next_member_id, name=name, email=email, joined=str(datetime.now().date()))\n'
                '        self._next_member_id += 1\n'
                '        self.members.append(m)\n'
                '        return m\n\n'
                '    def find_member(self, member_id: int) -> Optional[Member]:\n'
                '        for m in self.members:\n'
                '            if m.id == member_id:\n'
                '                return m\n'
                '        return None\n\n'
                '    def deactivate_member(self, member_id: int) -> bool:\n'
                '        m = self.find_member(member_id)\n'
                '        if m:\n'
                '            m.active = False\n'
                '            return True\n'
                '        return False\n\n'
                '    # ── Loan operations ──\n'
                '    def borrow_book(self, book_id: int, member_id: int) -> Optional[Loan]:\n'
                '        book = self.find_book(book_id)\n'
                '        member = self.find_member(member_id)\n'
                '        if not book or not member:\n'
                '            return None\n'
                '        if not book.available:\n'
                '            return None\n'
                '        if not member.active:\n'
                '            return None\n'
                '        if member.fines_due > 0:\n'
                '            return None\n'
                '        today = str(datetime.now().date())\n'
                '        due = str(datetime.now().date() + timedelta(days=14))\n'
                '        loan = Loan(id=self._next_loan_id, book_id=book_id, member_id=member_id, borrowed=today, due=due)\n'
                '        self._next_loan_id += 1\n'
                '        book.available = False\n'
                '        self.loans.append(loan)\n'
                '        return loan\n\n'
                '    def return_book(self, loan_id: int) -> Optional[float]:\n'
                '        """Returns the book. Returns fine amount if overdue, or 0."""\n'
                '        loan = None\n'
                '        for l in self.loans:\n'
                '            if l.id == loan_id and l.returned is None:\n'
                '                loan = l\n'
                '                break\n'
                '        if not loan:\n'
                '            return None\n'
                '        book = self.find_book(loan.book_id)\n'
                '        if book:\n'
                '            book.available = True\n'
                '        loan.returned = str(datetime.now().date())\n'
                '        due_date = datetime.strptime(loan.due, "%Y-%m-%d")\n'
                '        today = datetime.now().date()\n'
                '        if today > due_date.date():\n'
                '            days_late = (today - due_date.date()).days\n'
                '            fine = days_late * 0.50\n'
                '            member = self.find_member(loan.member_id)\n'
                '            if member:\n'
                '                member.fines_due += fine\n'
                '            return fine\n'
                '        return 0.0\n\n'
                '    def get_member_loans(self, member_id: int) -> list[Loan]:\n'
                '        return [l for l in self.loans if l.member_id == member_id]\n\n'
                '    def get_overdue_loans(self) -> list[Loan]:\n'
                '        today = datetime.now().date()\n'
                '        overdue = []\n'
                '        for l in self.loans:\n'
                '            if l.returned is None:\n'
                '                due = datetime.strptime(l.due, "%Y-%m-%d").date()\n'
                '                if today > due:\n'
                '                    overdue.append(l)\n'
                '        return overdue\n\n'
                '    # ── Reporting ──\n'
                '    def generate_report(self) -> dict:\n'
                '        total_books = len(self.books)\n'
                '        available = len(self.list_available_books())\n'
                '        total_members = len(self.members)\n'
                '        active_loans = len([l for l in self.loans if l.returned is None])\n'
                '        total_fines = sum(m.fines_due for m in self.members)\n'
                '        overdue = self.get_overdue_loans()\n'
                '        return {\n'
                '            "total_books": total_books,\n'
                '            "available_books": available,\n'
                '            "total_members": total_members,\n'
                '            "active_loans": active_loans,\n'
                '            "overdue_loans": len(overdue),\n'
                '            "total_fines_due": round(total_fines, 2),\n'
                '        }\n'
            ),
            "README.md": "# Library Management System\n\nMonolithic system — needs refactoring into modular components.\n",
        },
        "expected_artifacts": ["REFACTOR_PLAN.md", "test_library.py"],
    },
    {
        "session": 2,
        "title": "Session 2: Execute Refactor with Sub-Agents",
        "prompt": (
            "# Project: Library Management System Refactor — Session 2 of 2\n\n"
            "You MUST use sub-agents (Task/Agent dispatching) for this session.\n\n"
            "Split the monolithic `library.py` into these modules, each handled by a sub-agent:\n\n"
            "1. **Sub-Agent A: `books.py`** — Book class, BookRepository (add/find/search/list)\n"
            "2. **Sub-Agent B: `members.py`** — Member class, MemberRepository\n"
            "3. **Sub-Agent C: `loans.py`** — Loan class, LoanService (borrow/return/get_overdue/get_member_loans)\n"
            "4. **Sub-Agent D: `reporting.py`** — ReportService (generates reports using the other modules)\n"
            "5. **Main: `library.py`** — Updated to import and coordinate the modules\n\n"
            "Requirements:\n"
            "- Each sub-agent produces its own file with tests\n"
            "- All existing tests in `test_library.py` must still pass AFTER the refactor\n"
            "- Create a `REFACTOR_SUMMARY.md` documenting which sub-agent handled what "
            "and how the modules communicate\n\n"
            "This validates your multi-agent coordination: dispatching, result merging, "
            "and consistency checking across agents."
        ),
    },
]


def main():
    for proj_idx, sessions in enumerate([P1_SESSIONS, P2_SESSIONS], 1):
        project_id = f"L3-PROJECT-{proj_idx:03d}"
        project_dir = ITEMS_DIR / project_id

        for sess in sessions:
            session_dir = project_dir / f"session_{sess['session']}"
            context_dir = session_dir / "context"
            judge_dir = session_dir / "judge"
            context_dir.mkdir(parents=True, exist_ok=True)
            judge_dir.mkdir(parents=True, exist_ok=True)

            # Write seed files if any
            files = sess.get("files", {})
            for filename, content in files.items():
                fp = context_dir / filename
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(content)

            metadata = {
                "id": f"{project_id}-S{sess['session']}",
                "layer": "L3",
                "dimensions": ["D2", "D4", "D6"],
                "sub_dimensions": ["D1", "D3", "D5"],
                "language": "python",
                "difficulty": 4 if proj_idx == 1 else 5,
                "estimated_time_min": 90,
                "tags": (
                    ["memory", "multi-session", "api", "iteration"]
                    if proj_idx == 1
                    else ["multi-agent", "refactor", "coordination"]
                ),
                "sandbox": {
                    "image": "python",
                    "dependencies": ["pytest", "flask", "sqlalchemy", "pyjwt"],
                    "network": "none",
                },
                "prompt_template": sess["prompt"],
                "context_files": [
                    str(Path("context") / f) for f in files.keys()
                ],
                "expected_artifacts": sess.get("expected_artifacts", []),
                "scoring": {"type": "llm_judge", "pass_threshold": 0.65},
                "created": "2026-07-15",
                "version": "1.0",
            }
            (session_dir / "metadata.json").write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False)
            )
            print(f"Created {metadata['id']}: {sess['title']}")

    # Update registry
    with open(ITEMS_DIR.parent / "registry.json") as f:
        reg = json.load(f)

    all_ids = [
        f"L3-PROJECT-001-S{s}" for s in range(1, 4)
    ] + [
        f"L3-PROJECT-002-S{s}" for s in range(1, 3)
    ]
    for item_id in all_ids:
        entry = {"id": item_id, "path": f"l3/{item_id[:12]}/{item_id}", "enabled": True}
        if entry not in reg["items"]:
            reg["items"].append(entry)
    with open(ITEMS_DIR.parent / "registry.json", "w") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
    print(f"Registry updated: {len(reg['items'])} items total")


if __name__ == "__main__":
    main()
