"""Generate 8 D2 decomposition + 7 D5 code review items."""
import json
from pathlib import Path

ITEMS_DIR = Path(__file__).parent.parent / "test_items" / "l1"

# ── 8 D2 Task Decomposition Items (tree_sim scoring) ──
DECOMPOSE_ITEMS = [
    {
        "id": "L1-D2-DC-001", "difficulty": 1,
        "tags": ["decompose", "simple"],
        "prompt": (
            "Decompose this requirement into subtasks:\n"
            '"Add a health-check endpoint GET /health that returns {\"status\": \"ok\"}"\n'
            "Output a JSON tree: {\"task\": \"<main>\", \"subtasks\": [{\"task\": \"<sub>\", \"subtasks\": []}]}"
        ),
        "expected_tree": json.dumps({
            "task": "Add health-check endpoint",
            "subtasks": [
                {"task": "Define route GET /health", "subtasks": []},
                {"task": "Return JSON response", "subtasks": []},
                {"task": "Test endpoint", "subtasks": []},
            ]
        }),
    },
    {
        "id": "L1-D2-DC-002", "difficulty": 1,
        "tags": ["decompose", "simple"],
        "prompt": (
            "Decompose into subtasks:\n"
            '"Create a Python script that reads a CSV file and prints the row count."\n'
            "Output JSON tree format."
        ),
        "expected_tree": json.dumps({
            "task": "Create CSV row counter script",
            "subtasks": [
                {"task": "Read CSV file path from args", "subtasks": []},
                {"task": "Parse CSV rows", "subtasks": []},
                {"task": "Count and print row count", "subtasks": []},
            ]
        }),
    },
    {
        "id": "L1-D2-DC-003", "difficulty": 2,
        "tags": ["decompose", "web"],
        "prompt": (
            "Decompose into subtasks with dependencies:\n"
            '"Build a login page with email/password fields and a submit button."\n'
            "Output JSON tree format."
        ),
        "expected_tree": json.dumps({
            "task": "Build login page",
            "subtasks": [
                {"task": "Create HTML form", "subtasks": []},
                {"task": "Add CSS styling", "subtasks": []},
                {"task": "Implement client-side validation", "subtasks": []},
                {"task": "Connect to backend auth API", "subtasks": []},
                {"task": "Handle error states", "subtasks": []},
            ]
        }),
    },
    {
        "id": "L1-D2-DC-004", "difficulty": 2,
        "tags": ["decompose", "database"],
        "prompt": (
            "Decompose into subtasks:\n"
            '"Add a users table to the database and create CRUD API endpoints."\n'
            "Output JSON tree."
        ),
        "expected_tree": json.dumps({
            "task": "Add users CRUD",
            "subtasks": [
                {"task": "Create migration for users table", "subtasks": []},
                {"task": "Define Users model", "subtasks": []},
                {"task": "Build POST /users endpoint", "subtasks": []},
                {"task": "Build GET /users endpoint", "subtasks": []},
                {"task": "Build PUT /users/:id endpoint", "subtasks": []},
                {"task": "Build DELETE /users/:id endpoint", "subtasks": []},
                {"task": "Add tests", "subtasks": []},
            ]
        }),
    },
    {
        "id": "L1-D2-DC-005", "difficulty": 3,
        "tags": ["decompose", "optimize"],
        "prompt": (
            "Decompose into subtasks:\n"
            '"The homepage loads slowly. Investigate causes and optimize to under 2 seconds."\n'
            "Output JSON tree."
        ),
        "expected_tree": json.dumps({
            "task": "Optimize homepage load time",
            "subtasks": [
                {"task": "Profile page load performance", "subtasks": []},
                {"task": "Identify slow queries", "subtasks": []},
                {"task": "Add database indexes", "subtasks": []},
                {"task": "Implement caching", "subtasks": []},
                {"task": "Optimize asset delivery", "subtasks": []},
                {"task": "Verify performance improvement", "subtasks": []},
            ]
        }),
    },
    {
        "id": "L1-D2-DC-006", "difficulty": 4,
        "tags": ["decompose", "migration"],
        "prompt": (
            "Decompose into subtasks:\n"
            '"Migrate this monolith Express.js app to a microservices architecture '
            'with separate auth, users, and products services."\n'
            "Output JSON tree."
        ),
        "expected_tree": json.dumps({
            "task": "Migrate to microservices",
            "subtasks": [
                {"task": "Analyze current monolith structure", "subtasks": []},
                {"task": "Design service boundaries and APIs", "subtasks": []},
                {"task": "Extract auth service", "subtasks": []},
                {"task": "Extract users service", "subtasks": []},
                {"task": "Extract products service", "subtasks": []},
                {"task": "Implement API gateway", "subtasks": []},
                {"task": "Add inter-service communication", "subtasks": []},
                {"task": "Update deployment pipeline", "subtasks": []},
            ]
        }),
    },
    {
        "id": "L1-D2-DC-007", "difficulty": 4,
        "tags": ["decompose", "security"],
        "prompt": (
            "Decompose into subtasks:\n"
            '"Implement JWT authentication with refresh tokens, rate limiting, '
            'and OAuth2 Google login for the existing API."\n'
            "Output JSON tree."
        ),
        "expected_tree": json.dumps({
            "task": "Implement JWT + OAuth2 auth",
            "subtasks": [
                {"task": "Add JWT token generation and validation", "subtasks": []},
                {"task": "Implement refresh token flow", "subtasks": []},
                {"task": "Add OAuth2 Google login integration", "subtasks": []},
                {"task": "Implement rate limiting middleware", "subtasks": []},
                {"task": "Protect existing API routes", "subtasks": []},
                {"task": "Add auth tests", "subtasks": []},
                {"task": "Update API documentation", "subtasks": []},
            ]
        }),
    },
    {
        "id": "L1-D2-DC-008", "difficulty": 5,
        "tags": ["decompose", "fullstack"],
        "prompt": (
            "Decompose into subtasks:\n"
            '"Build a real-time collaborative text editor with WebSocket sync, '
            'operational transform, user presence, and version history."\n'
            "Output JSON tree."
        ),
        "expected_tree": json.dumps({
            "task": "Build collaborative text editor",
            "subtasks": [
                {"task": "Design document model and OT algorithm", "subtasks": []},
                {"task": "Implement WebSocket server", "subtasks": []},
                {"task": "Build text editor UI component", "subtasks": []},
                {"task": "Implement operational transform engine", "subtasks": []},
                {"task": "Add user presence system", "subtasks": []},
                {"task": "Implement version history storage", "subtasks": []},
                {"task": "Add conflict resolution", "subtasks": []},
                {"task": "Build version diff viewer", "subtasks": []},
                {"task": "Write integration tests", "subtasks": []},
            ]
        }),
    },
]

# ── 7 D5 Code Review Items (LLM-as-Judge scoring) ──
REVIEW_ITEMS = [
    {
        "id": "L1-D5-RV-001", "difficulty": 1,
        "tags": ["review", "security", "sql-injection"],
        "prompt": (
            "Review the following code diff for a PR. Identify all issues:\n\n"
            "```diff\n"
            "+ def get_user(user_id):\n"
            "+     query = \"SELECT * FROM users WHERE id = \" + user_id\n"
            "+     return db.execute(query)\n"
            "```\n\n"
            "List each issue with: file location, severity (critical/high/medium/low), "
            "description, and suggested fix."
        ),
        "expected_issues": [
            "SQL injection vulnerability — user_id concatenated directly into query",
            "Use parameterized queries or ORM",
        ],
        "scoring_type": "llm_judge",
    },
    {
        "id": "L1-D5-RV-002", "difficulty": 1,
        "tags": ["review", "error-handling"],
        "prompt": (
            "Review this code and find issues:\n\n"
            "```python\n"
            "def read_config(path):\n"
            "    data = open(path).read()\n"
            "    return json.loads(data)\n"
            "```\n\n"
            "List each issue with severity and suggested fix."
        ),
        "expected_issues": [
            "File not closed — resource leak, use context manager",
            "No FileNotFoundError handling",
            "No JSON decode error handling",
        ],
        "scoring_type": "llm_judge",
    },
    {
        "id": "L1-D5-RV-003", "difficulty": 2,
        "tags": ["review", "performance"],
        "prompt": (
            "Review for issues:\n\n"
            "```python\n"
            "def find_user(users: list[dict], email: str) -> dict | None:\n"
            "    for user in users:\n"
            "        if user['email'] == email:\n"
            "            return user\n"
            "    return None\n"
            "```\n\n"
            "Context: This function is called in a loop over 100k users repeatedly.\n"
            "List issues with severity and suggested fix."
        ),
        "expected_issues": [
            "O(n) lookup called in loop — O(n²) total, build a dict/index first",
            "No handling if 'email' key missing from user dict",
        ],
        "scoring_type": "llm_judge",
    },
    {
        "id": "L1-D5-RV-004", "difficulty": 2,
        "tags": ["review", "concurrency"],
        "prompt": (
            "Review for issues:\n\n"
            "```python\n"
            "class Counter:\n"
            "    def __init__(self):\n"
            "        self.count = 0\n"
            "    def increment(self):\n"
            "        self.count += 1\n"
            "    def get(self):\n"
            "        return self.count\n"
            "```\n\n"
            "Context: Used by multiple threads in a web server.\n"
            "List issues with severity and suggested fix."
        ),
        "expected_issues": [
            "count += 1 is not thread-safe — race condition",
            "Use threading.Lock or atomic operations",
        ],
        "scoring_type": "llm_judge",
    },
    {
        "id": "L1-D5-RV-005", "difficulty": 3,
        "tags": ["review", "API-design"],
        "prompt": (
            "Review this API endpoint for issues:\n\n"
            "```python\n"
            "@app.post('/api/users')\n"
            "def create_user():\n"
            "    data = request.get_json()\n"
            "    user = User(\n"
            "        name=data['name'],\n"
            "        email=data['email'],\n"
            "        password=data['password']\n"
            "    )\n"
            "    db.session.add(user)\n"
            "    db.session.commit()\n"
            "    return jsonify(user.to_dict()), 201\n"
            "```\n\n"
            "List all issues with severity and fix suggestions."
        ),
        "expected_issues": [
            "Password stored in plaintext — must hash before storing",
            "No input validation — blank names, invalid emails",
            "No duplicate email check — unique constraint violation",
            "No error handling — missing fields cause KeyError",
        ],
        "scoring_type": "llm_judge",
    },
    {
        "id": "L1-D5-RV-006", "difficulty": 4,
        "tags": ["review", "security", "crypto"],
        "prompt": (
            "Review this auth module for issues:\n\n"
            "```python\n"
            "import hashlib\n"
            "import base64\n\n"
            "SECRET = 'my-secret-key'\n\n"
            "def generate_token(user_id: int) -> str:\n"
            "    payload = f'{user_id}:{SECRET}'\n"
            "    return base64.b64encode(payload.encode()).decode()\n\n"
            "def validate_token(token: str) -> int | None:\n"
            "    try:\n"
            "        payload = base64.b64decode(token).decode()\n"
            "        user_id, secret = payload.split(':')\n"
            "        if secret == SECRET:\n"
            "            return int(user_id)\n"
            "    except:\n"
            "        pass\n"
            "    return None\n"
            "```\n\n"
            "List all issues with severity and suggested fix."
        ),
        "expected_issues": [
            "Hardcoded secret — use env var or config",
            "No cryptographic signing — token is forgeable (just base64)",
            "Use JWT or HMAC instead of base64 encoding",
            "Bare except hides all errors",
            "No token expiration — tokens valid forever",
            "hashlib imported but unused",
        ],
        "scoring_type": "llm_judge",
    },
    {
        "id": "L1-D5-RV-007", "difficulty": 5,
        "tags": ["review", "architecture"],
        "prompt": (
            "Review this payment processing module for issues:\n\n"
            "```python\n"
            "class PaymentProcessor:\n"
            "    def __init__(self, db_session):\n"
            "        self.db = db_session\n\n"
            "    def process(self, user_id, amount, card_token):\n"
            "        user = self.db.query(User).get(user_id)\n"
            "        if user.balance < amount:\n"
            "            raise ValueError('Insufficient funds')\n"
            "        charge = stripe.Charge.create(\n"
            "            amount=amount, currency='usd', source=card_token)\n"
            "        user.balance -= amount\n"
            "        order = Order(user_id=user_id, amount=amount, status='paid')\n"
            "        self.db.add(order)\n"
            "        self.db.commit()\n"
            "        send_email(user.email, 'Payment confirmed', f'Charged ${amount}')\n"
            "        return order\n"
            "```\n\n"
            "List all issues with severity and suggested fix."
        ),
        "expected_issues": [
            "No idempotency — duplicate requests charge twice",
            "Stripe charge before DB commit — charge succeeds but order may fail to save",
            "Email send inside transaction — blocks on network, no retry",
            "Balance check race condition between two concurrent requests",
            "Stripe API key not shown but presumably hardcoded/inline",
            "No logging or audit trail",
            "Amount in dollars but balance check compares directly",
            "No retry or rollback on Stripe failure",
        ],
        "scoring_type": "llm_judge",
    },
]


def main():
    all_items = []

    # Decomposition items
    for item in DECOMPOSE_ITEMS:
        item_dir = ITEMS_DIR / "d2_decompose" / item["id"]
        context_dir = item_dir / "context"
        judge_dir = item_dir / "judge"
        context_dir.mkdir(parents=True, exist_ok=True)
        judge_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "id": item["id"],
            "layer": "L1",
            "dimensions": ["D2"],
            "sub_dimensions": [],
            "language": "any",
            "difficulty": item["difficulty"],
            "estimated_time_min": item["difficulty"] * 5,
            "tags": item["tags"],
            "sandbox": {
                "image": "python", "dependencies": [], "network": "none",
            },
            "prompt_template": item["prompt"],
            "context_files": [],
            "expected_artifacts": [],
            "scoring": {
                "type": "tree_sim",
                "expected_tree": item["expected_tree"],
                "tree_threshold": 0.6,
            },
            "created": "2026-07-01",
            "version": "1.0",
        }
        (item_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False)
        )
        (context_dir / ".gitkeep").write_text("")
        (judge_dir / ".gitkeep").write_text("")
        all_items.append(("d2_decompose", item["id"]))
        print(f"Created {item['id']} (difficulty {item['difficulty']})")

    # Code review items
    for item in REVIEW_ITEMS:
        item_dir = ITEMS_DIR / "d5_code_review" / item["id"]
        context_dir = item_dir / "context"
        judge_dir = item_dir / "judge"
        context_dir.mkdir(parents=True, exist_ok=True)
        judge_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "id": item["id"],
            "layer": "L1",
            "dimensions": ["D5"],
            "sub_dimensions": [],
            "language": "python",
            "difficulty": item["difficulty"],
            "estimated_time_min": item["difficulty"] * 6,
            "tags": item["tags"],
            "sandbox": {
                "image": "python", "dependencies": [], "network": "none",
            },
            "prompt_template": item["prompt"],
            "context_files": [],
            "expected_artifacts": [],
            "scoring": {
                "type": "llm_judge",
                "test_command": "",
                "pass_threshold": 0.0,
            },
            "created": "2026-07-01",
            "version": "1.0",
        }
        (item_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False)
        )
        (context_dir / ".gitkeep").write_text("")
        (judge_dir / "expected_issues.json").write_text(
            json.dumps(item["expected_issues"], indent=2)
        )
        all_items.append(("d5_code_review", item["id"]))
        print(f"Created {item['id']} (difficulty {item['difficulty']})")

    # Update registry
    with open(ITEMS_DIR.parent / "registry.json") as f:
        reg = json.load(f)
    for subdir, item_id in all_items:
        entry = {"id": item_id, "path": f"l1/{subdir}/{item_id}", "enabled": True}
        if entry not in reg["items"]:
            reg["items"].append(entry)
    with open(ITEMS_DIR.parent / "registry.json", "w") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
    print(f"Registry updated: {len(reg['items'])} items total")


if __name__ == "__main__":
    main()
