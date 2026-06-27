"""Generate 10 D3 tool selection & chaining test items."""
import json
from pathlib import Path

ITEMS_DIR = Path(__file__).parent.parent / "test_items" / "l1"

# ── 5 Tool Selection Items ──
SELECT_ITEMS = [
    {
        "id": "L1-D3-ST-001", "difficulty": 1,
        "tags": ["file-read", "tool-select"],
        "prompt": (
            "You need to read the contents of the file `/project/src/config.py`. "
            "Use exactly one tool call with the correct tool name and parameter `file_path`."
        ),
        "scoring": {
            "type": "tool_match",
            "tool_sequence": ["Read"],
            "key_params": ["file_path"],
        },
    },
    {
        "id": "L1-D3-ST-002", "difficulty": 1,
        "tags": ["search", "tool-select"],
        "prompt": (
            "Find all occurrences of the pattern `TODO` in all `.py` files "
            "under the `/project/src/` directory. Use a search/grep tool "
            "with parameters `pattern` and `path`."
        ),
        "scoring": {
            "type": "tool_match",
            "tool_sequence": ["Grep"],
            "key_params": ["pattern", "path"],
        },
    },
    {
        "id": "L1-D3-ST-003", "difficulty": 2,
        "tags": ["execution", "tool-select"],
        "prompt": (
            "Run the test suite located at `/project/tests/` using pytest. "
            "Use a shell/bash execution tool with parameter `command` set to "
            "`pytest /project/tests/ -v`."
        ),
        "scoring": {
            "type": "tool_match",
            "tool_sequence": ["Bash"],
            "key_params": ["command"],
        },
    },
    {
        "id": "L1-D3-ST-004", "difficulty": 2,
        "tags": ["file-write", "tool-select"],
        "prompt": (
            "Create a new file `/project/src/utils.py` with the content "
            "`import os\\n\\ndef get_env(key): return os.getenv(key)`. "
            "Use a file write/create tool with parameters `file_path` and `content`."
        ),
        "scoring": {
            "type": "tool_match",
            "tool_sequence": ["Write"],
            "key_params": ["file_path", "content"],
        },
    },
    {
        "id": "L1-D3-ST-005", "difficulty": 3,
        "tags": ["replace", "tool-select"],
        "prompt": (
            "In file `/project/src/main.py`, replace the line "
            "`DEBUG = True` with `DEBUG = False`. "
            "Use an edit/replace tool with parameters `file_path`, `old_string`, and `new_string`."
        ),
        "scoring": {
            "type": "tool_match",
            "tool_sequence": ["Edit"],
            "key_params": ["file_path", "old_string", "new_string"],
        },
    },
]

# ── 5 Tool Chaining Items ──
CHAIN_ITEMS = [
    {
        "id": "L1-D3-CH-001", "difficulty": 3,
        "tags": ["chain", "read-edit"],
        "prompt": (
            "Read `/project/README.md`, then update it by replacing all "
            "occurrences of `2025` with `2026`. Use Read then Edit tools in order."
        ),
        "scoring": {
            "type": "tool_match",
            "tool_sequence": ["Read", "Edit"],
            "key_params": ["file_path"],
        },
    },
    {
        "id": "L1-D3-CH-002", "difficulty": 3,
        "tags": ["chain", "search-read-edit"],
        "prompt": (
            "Search for files containing `FIXME` under `/project/src/`, "
            "then for each file found, read it to understand the issue, "
            "and fix the first one. Use Grep → Read → Edit in sequence."
        ),
        "scoring": {
            "type": "tool_match",
            "tool_sequence": ["Grep", "Read", "Edit"],
            "key_params": ["pattern", "file_path"],
        },
    },
    {
        "id": "L1-D3-CH-003", "difficulty": 4,
        "tags": ["chain", "write-test"],
        "prompt": (
            "Write a new Python file `/project/src/calculator.py` with a "
            "`def add(a, b): return a + b` function, then write a test file "
            "at `/project/tests/test_calculator.py`, then run pytest on it. "
            "Use Write → Write → Bash in sequence."
        ),
        "scoring": {
            "type": "tool_match",
            "tool_sequence": ["Write", "Write", "Bash"],
            "key_params": ["file_path", "command"],
        },
    },
    {
        "id": "L1-D3-CH-004", "difficulty": 4,
        "tags": ["chain", "list-read-execute"],
        "prompt": (
            "List files in `/project/data/`, read the first `.csv` file found, "
            "then run the Python script `/project/scripts/process.py` with that "
            "filename as an argument. Use an LS/Glob tool → Read → Bash sequence."
        ),
        "scoring": {
            "type": "tool_match",
            "tool_sequence": ["Glob", "Read", "Bash"],
            "key_params": ["pattern", "file_path", "command"],
        },
    },
    {
        "id": "L1-D3-CH-005", "difficulty": 5,
        "tags": ["chain", "complex-workflow"],
        "prompt": (
            "Perform the following workflow in order:\n"
            "1. Search for all Python files that import `deprecated_lib`\n"
            "2. Read each file to understand its usage\n"
            "3. Replace `import deprecated_lib` with `import new_lib` in each file\n"
            "4. Run the test suite to verify nothing broke\n"
            "Use Grep → Read → Edit → Bash in exact sequence."
        ),
        "scoring": {
            "type": "tool_match",
            "tool_sequence": ["Grep", "Read", "Edit", "Bash"],
            "key_params": ["pattern", "file_path", "old_string", "new_string", "command"],
        },
    },
]

ALL = SELECT_ITEMS + CHAIN_ITEMS


def main():
    for item in ALL:
        subdir = "d3_tool_select" if item["id"].startswith("L1-D3-ST") else "d3_tool_chain"
        item_dir = ITEMS_DIR / subdir / item["id"]
        context_dir = item_dir / "context"
        judge_dir = item_dir / "judge"
        context_dir.mkdir(parents=True, exist_ok=True)
        judge_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "id": item["id"],
            "layer": "L1",
            "dimensions": ["D3"],
            "sub_dimensions": [],
            "language": "any",
            "difficulty": item["difficulty"],
            "estimated_time_min": item["difficulty"] * 3,
            "tags": item["tags"],
            "sandbox": {
                "image": "python",
                "dependencies": [],
                "network": "none",
            },
            "prompt_template": item["prompt"],
            "context_files": [],
            "expected_artifacts": [],
            "scoring": item["scoring"],
            "created": "2026-07-01",
            "version": "1.0",
        }
        (item_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False)
        )
        # Create empty placeholder files to satisfy directory structure
        (context_dir / ".gitkeep").write_text("")
        (judge_dir / ".gitkeep").write_text("")
        print(f"Created {item['id']} (difficulty {item['difficulty']})")

    # Update registry
    with open(ITEMS_DIR.parent / "registry.json") as f:
        reg = json.load(f)
    for item in ALL:
        subdir = "d3_tool_select" if item["id"].startswith("L1-D3-ST") else "d3_tool_chain"
        entry = {"id": item["id"], "path": f"l1/{subdir}/{item['id']}", "enabled": True}
        if entry not in reg["items"]:
            reg["items"].append(entry)
    with open(ITEMS_DIR.parent / "registry.json", "w") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
    print(f"Registry updated: {len(reg['items'])} items total")


if __name__ == "__main__":
    main()
