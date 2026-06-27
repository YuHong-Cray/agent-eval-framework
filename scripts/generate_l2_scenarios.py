"""Generate 4 L2 integration scenarios with seed project contexts."""
import json
from pathlib import Path

ITEMS_DIR = Path(__file__).parent.parent / "test_items" / "l2"

SCENARIOS = [
    # ── Scenario 1: Auth Middleware ──
    {
        "id": "L2-SCENARIO-001",
        "title": "Add JWT Auth Middleware to REST API",
        "difficulty": 3,
        "tags": ["auth", "middleware", "api"],
        "prompt": (
            "# Task: Add JWT Authentication Middleware\n\n"
            "In the provided Flask REST API project (`app.py`), implement JWT-based "
            "authentication middleware that:\n\n"
            "1. Validates a Bearer token from the `Authorization` header on every "
            "request to `/api/*` endpoints\n"
            "2. Returns 401 with `{\"error\": \"unauthorized\"}` for invalid/missing tokens\n"
            "3. Adds the decoded user_id to `request.user_id` for downstream handlers\n"
            "4. Tokens are signed with HS256 using a secret from env var `JWT_SECRET`\n"
            "5. Include a `/auth/login` endpoint that accepts `{\"username\":\"...\", "
            "\"password\":\"...\"}` and returns a JWT token if credentials match "
            "(hardcoded demo user: admin/admin123)\n\n"
            "Deliverables: updated `app.py`, `requirements.txt` with PyJWT, "
            "and `test_auth.py` with at least 3 test cases."
        ),
        "files": {
            "app.py": (
                'from flask import Flask, request, jsonify\n\n'
                'app = Flask(__name__)\n\n'
                '@app.route("/api/hello")\n'
                'def hello():\n'
                '    return jsonify({"message": "Hello, World!"})\n\n'
                '@app.route("/api/users")\n'
                'def list_users():\n'
                '    return jsonify({"users": []})\n\n'
                'if __name__ == "__main__":\n'
                '    app.run(debug=True)\n'
            ),
            "requirements.txt": "flask==3.0.0\n",
            "README.md": "# Simple Flask API\n\nA minimal REST API.\n",
        },
        "expected_artifacts": ["app.py", "requirements.txt", "test_auth.py"],
    },
    # ── Scenario 2: Data Migration Script ──
    {
        "id": "L2-SCENARIO-002",
        "title": "Write a Data Migration Script with Validation",
        "difficulty": 3,
        "tags": ["data", "migration", "validation"],
        "prompt": (
            "# Task: Data Migration Script\n\n"
            "In the provided project, there are two JSON data files: "
            "`old_users.json` (legacy format) and `new_users_schema.json` (target schema).\n\n"
            "Write `migrate.py` that:\n\n"
            "1. Reads `old_users.json` which has flat user records with fields: "
            "`id`, `first_name`, `last_name`, `email`, `created`\n"
            "2. Transforms each record to match `new_users_schema.json`: "
            "`id`, `full_name` (first + last), `email` (validated), "
            "`profile` (object with `created_at`), `active` (default true)\n"
            "3. Validates that emails contain '@' — skip and log invalid records\n"
            "4. Writes output to `new_users.json`\n"
            "5. Prints a summary: 'Migrated X users, skipped Y invalid'\n\n"
            "Deliverables: `migrate.py` and `test_migrate.py`."
        ),
        "files": {
            "old_users.json": json.dumps([
                {"id": 1, "first_name": "Alice", "last_name": "Smith", "email": "alice@example.com", "created": "2024-01-15"},
                {"id": 2, "first_name": "Bob", "last_name": "Jones", "email": "bob-invalid", "created": "2024-02-20"},
                {"id": 3, "first_name": "Charlie", "last_name": "Brown", "email": "charlie@test.org", "created": "2024-03-10"},
            ], indent=2),
            "new_users_schema.json": json.dumps({
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "full_name": {"type": "string"},
                    "email": {"type": "string"},
                    "profile": {"type": "object", "properties": {"created_at": {"type": "string"}}},
                    "active": {"type": "boolean"},
                },
            }, indent=2),
            "README.md": "# User Data Migration\n\nMigrate old user format to new schema.\n",
        },
        "expected_artifacts": ["migrate.py", "test_migrate.py"],
    },
    # ── Scenario 3: Frontend Form Component ──
    {
        "id": "L2-SCENARIO-003",
        "title": "Build a React Signup Form with Validation",
        "difficulty": 3,
        "tags": ["frontend", "form", "react"],
        "prompt": (
            "# Task: Build a Signup Form Component\n\n"
            "In the provided React project, implement `src/SignupForm.jsx` that:\n\n"
            "1. Has fields: `username` (3-20 chars, alphanumeric), "
            "`email` (valid email format), `password` (min 8 chars, "
            "must contain 1 uppercase + 1 digit), `confirm_password` (must match)\n"
            "2. Shows inline validation errors below each field on blur\n"
            "3. Submit button disabled until all validations pass\n"
            "4. On submit, calls `props.onSubmit({username, email, password})`\n"
            "5. Shows a loading spinner while submitting (controlled by `props.loading`)\n"
            "6. Displays `props.error` as a banner if present\n\n"
            "Deliverables: `src/SignupForm.jsx` and `src/SignupForm.test.jsx`."
        ),
        "files": {
            "src/App.jsx": (
                'import React from "react";\n'
                'import SignupForm from "./SignupForm";\n\n'
                'function App() {\n'
                '  const handleSubmit = (data) => console.log("Submitted:", data);\n'
                '  return <SignupForm onSubmit={handleSubmit} loading={false} />;\n'
                '}\n\n'
                'export default App;\n'
            ),
            "src/SignupForm.jsx": "// TODO: Implement signup form component\n",
            "package.json": json.dumps({
                "name": "signup-form",
                "version": "1.0.0",
                "dependencies": {"react": "^18.2.0"},
                "devDependencies": {"@testing-library/react": "^14.0.0"},
            }, indent=2),
            "README.md": "# Signup Form Component\n\nImplement the SignupForm per requirements.\n",
        },
        "expected_artifacts": ["src/SignupForm.jsx", "src/SignupForm.test.jsx"],
    },
    # ── Scenario 4: Performance Optimization ──
    {
        "id": "L2-SCENARIO-004",
        "title": "Debug and Optimize a Slow API Endpoint",
        "difficulty": 4,
        "tags": ["performance", "optimization", "profiling"],
        "prompt": (
            "# Task: Optimize a Slow API Endpoint\n\n"
            "The provided `app.py` has a `/api/report` endpoint that generates a "
            "monthly sales report. It runs correctly but is too slow (should complete "
            "in under 100ms for 10k records, currently takes seconds).\n\n"
            "Your tasks:\n\n"
            "1. Profile the endpoint to identify performance bottlenecks\n"
            "2. Optimize the code — common issues include:\n"
            "   - N+1 database queries\n"
            "   - Inefficient in-memory operations\n"
            "   - Missing database indexes\n"
            "   - Unnecessary data copies\n"
            "3. Document all changes with before/after timing in `OPTIMIZATION.md`\n"
            "4. Ensure all existing tests still pass and add a performance test\n\n"
            "Deliverables: updated `app.py`, `OPTIMIZATION.md`, and updated `test_app.py`."
        ),
        "files": {
            "app.py": (
                '"""Sales report API — intentionally slow for optimization exercise."""\n'
                'import time\n'
                'from dataclasses import dataclass\n'
                'from typing import Optional\n'
                '\n'
                '@dataclass\n'
                'class Order:\n'
                '    id: int\n'
                '    user_id: int\n'
                '    product: str\n'
                '    amount: float\n'
                '    month: str\n'
                '\n'
                '# Simulated "database" with 10k records\n'
                'def _load_orders() -> list[Order]:\n'
                '    orders = []\n'
                '    products = ["Widget", "Gadget", "Doodad"]\n'
                '    months = ["2024-01", "2024-02", "2024-03"]\n'
                '    for i in range(10000):\n'
                '        orders.append(Order(\n'
                '            id=i,\n'
                '            user_id=i % 500,\n'
                '            product=products[i % 3],\n'
                '            amount=10.0 + (i % 100),\n'
                '            month=months[i % 3],\n'
                '        ))\n'
                '    return orders\n'
                '\n'
                '# BUG: loaded on every request instead of once\n'
                'def get_report(month: Optional[str] = None):\n'
                '    orders = _load_orders()  # BUG: regenerates every call\n'
                '    if month:\n'
                '        orders = [o for o in orders if o.month == month]\n'
                '    \n'
                '    # BUG: nested loops — O(n*m) instead of single pass\n'
                '    total = 0.0\n'
                '    by_product = {}\n'
                '    for p in ["Widget", "Gadget", "Doodad"]:\n'
                '        for o in orders:\n'
                '            if o.product == p:\n'
                '                total += o.amount\n'
                '                by_product[p] = by_product.get(p, 0.0) + o.amount\n'
                '    \n'
                '    # BUG: sort then list comp for no reason\n'
                '    sorted_orders = sorted(orders, key=lambda o: o.amount, reverse=True)\n'
                '    report = []\n'
                '    for o in sorted_orders:\n'
                '        report.append(o)\n'
                '    \n'
                '    return {\n'
                '        "total": total,\n'
                '        "by_product": by_product,\n'
                '        "top_orders": [\n'
                '            {"id": o.id, "amount": o.amount} for o in report[:5]\n'
                '        ],\n'
                '    }\n'
            ),
            "test_app.py": (
                'from app import get_report\n\n'
                'def test_get_report_all():\n'
                '    result = get_report()\n'
                '    assert "total" in result\n'
                '    assert "by_product" in result\n'
                '    assert len(result["top_orders"]) == 5\n\n'
                'def test_get_report_filtered():\n'
                '    result = get_report(month="2024-01")\n'
                '    assert result["total"] > 0\n'
            ),
            "README.md": "# Sales Report API\n\nOptimize the `/api/report` endpoint.\n",
        },
        "expected_artifacts": ["app.py", "OPTIMIZATION.md", "test_app.py"],
    },
]


def main():
    for scenario in SCENARIOS:
        item_dir = ITEMS_DIR / scenario["id"]
        context_dir = item_dir / "context"
        judge_dir = item_dir / "judge"
        context_dir.mkdir(parents=True, exist_ok=True)
        judge_dir.mkdir(parents=True, exist_ok=True)

        # Write seed project files into context/
        for filename, content in scenario["files"].items():
            filepath = context_dir / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content)

        metadata = {
            "id": scenario["id"],
            "layer": "L2",
            "dimensions": ["D1", "D2", "D3", "D5"],
            "sub_dimensions": ["D4", "D6"],
            "language": "python",
            "difficulty": scenario["difficulty"],
            "estimated_time_min": 45,
            "tags": scenario["tags"],
            "sandbox": {
                "image": "python",
                "dependencies": ["pytest", "pyjwt", "flask"],
                "network": "none",
            },
            "prompt_template": scenario["prompt"],
            "context_files": [
                str(Path("context") / f)
                for f in scenario["files"].keys()
            ],
            "expected_artifacts": scenario["expected_artifacts"],
            "scoring": {
                "type": "llm_judge",
                "pass_threshold": 0.70,
            },
            "created": "2026-07-10",
            "version": "1.0",
        }
        (item_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False)
        )
        print(f"Created {scenario['id']}: {scenario['title']}")

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
