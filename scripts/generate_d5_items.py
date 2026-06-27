"""Generate 10 D5 bug-fix test items."""
import json
from pathlib import Path

ITEMS_DIR = Path(__file__).parent.parent / "test_items" / "l1" / "d5_bug_fix"

ITEMS = [
    # D5-001: off-by-one error
    {
        "id": "L1-D5-PY-001", "difficulty": 1,
        "tags": ["array", "off-by-one"],
        "prompt": (
            "The function `sum_list` in `main.py` has a bug. "
            "Find and fix it so that all tests pass.\n"
            "The function should return the sum of all integers in the list."
        ),
        "buggy_code": (
            "def sum_list(items: list[int]) -> int:\n"
            "    total = 0\n"
            "    for i in range(len(items) - 1):\n"
            "        total += items[i]\n"
            "    return total\n"
        ),
        "tests": [
            "def test_nonempty():\n    assert sum_list([1, 2, 3, 4, 5]) == 15",
            "def test_empty():\n    assert sum_list([]) == 0",
            "def test_single():\n    assert sum_list([42]) == 42",
        ],
    },
    # D5-002: string mutation vs str immutability
    {
        "id": "L1-D5-PY-002", "difficulty": 1,
        "tags": ["string", "immutability"],
        "prompt": (
            "The function `remove_vowels` in `main.py` is supposed to remove "
            "all vowels from a string, but it crashes. Find and fix the bug.\n"
            "Example: 'hello world' -> 'hll wrld'"
        ),
        "buggy_code": (
            "def remove_vowels(s: str) -> str:\n"
            "    vowels = 'aeiouAEIOU'\n"
            "    result = list(s)\n"
            "    for i, ch in enumerate(result):\n"
            "        if ch in vowels:\n"
            "            del result[i]\n"
            "    return ''.join(result)\n"
        ),
        "tests": [
            "def test_basic():\n    assert remove_vowels('hello world') == 'hll wrld'",
            "def test_all_vowels():\n    assert remove_vowels('aeiou') == ''",
            "def test_no_vowels():\n    assert remove_vowels('rhythm') == 'rhythm'",
        ],
    },
    # D5-003: incorrect default argument (mutable default)
    {
        "id": "L1-D5-PY-003", "difficulty": 2,
        "tags": ["default-arg", "list"],
        "prompt": (
            "The function `add_item` in `main.py` has a subtle bug related to "
            "Python default arguments. Find and fix it so that tests pass."
        ),
        "buggy_code": (
            "def add_item(item: str, items: list[str] = []) -> list[str]:\n"
            "    items.append(item)\n"
            "    return items\n"
        ),
        "tests": [
            "def test_single_call():\n    assert add_item('a') == ['a']",
            "def test_multiple_calls_independent():\n"
            "    r1 = add_item('a')\n"
            "    r2 = add_item('b')\n"
            "    assert r1 == ['a']\n"
            "    assert r2 == ['b']",
        ],
    },
    # D5-004: integer division bug
    {
        "id": "L1-D5-PY-004", "difficulty": 2,
        "tags": ["math", "division"],
        "prompt": (
            "The function `average` in `main.py` returns wrong results for "
            "integer lists. Fix the bug.\n"
            "Example: [1, 2, 3, 4] -> 2.5"
        ),
        "buggy_code": (
            "def average(items: list[int]) -> float:\n"
            "    if not items:\n"
            "        return 0.0\n"
            "    return sum(items) / len(items)  # bug in Python 2?\n"
        ),
        "tests": [
            "def test_basic():\n    assert average([1, 2, 3, 4]) == 2.5",
            "def test_integers():\n    assert average([1, 2]) == 1.5",
            "def test_empty():\n    assert average([]) == 0.0",
        ],
    },
    # D5-005: recursion missing base case
    {
        "id": "L1-D5-PY-005", "difficulty": 2,
        "tags": ["recursion", "base-case"],
        "prompt": (
            "The function `factorial` in `main.py` causes infinite recursion "
            "for some inputs. Find and fix the bug."
        ),
        "buggy_code": (
            "def factorial(n: int) -> int:\n"
            "    return n * factorial(n - 1)\n"
        ),
        "tests": [
            "def test_base():\n    assert factorial(0) == 1",
            "def test_pos():\n    assert factorial(5) == 120",
            "def test_one():\n    assert factorial(1) == 1",
        ],
    },
    # D5-006: logic error in comparison
    {
        "id": "L1-D5-PY-006", "difficulty": 3,
        "tags": ["logic", "comparison"],
        "prompt": (
            "The function `is_palindrome` in `main.py` has a logic bug. "
            "Fix it to correctly identify palindromes.\n"
            "A palindrome reads the same forward and backward."
        ),
        "buggy_code": (
            "def is_palindrome(s: str) -> bool:\n"
            "    s = s.lower().replace(' ', '')\n"
            "    for i in range(len(s)):\n"
            "        if s[i] != s[-i]:  # bug here\n"
            "            return False\n"
            "    return True\n"
        ),
        "tests": [
            "def test_pal():\n    assert is_palindrome('racecar') is True",
            "def test_not_pal():\n    assert is_palindrome('hello') is False",
            "def test_pal_spaces():\n    assert is_palindrome('a man a plan a canal panama') is True",
        ],
    },
    # D5-007: scope/closure bug
    {
        "id": "L1-D5-PY-007", "difficulty": 3,
        "tags": ["closure", "scope"],
        "prompt": (
            "The function `make_multipliers` in `main.py` should return a list "
            "of functions that each multiply by a different number. "
            "Find and fix the closure bug.\n"
            "Example: [m(5) for m in make_multipliers()] should be [0, 5, 10]"
        ),
        "buggy_code": (
            "def make_multipliers() -> list:\n"
            "    return [lambda x: i * x for i in range(3)]\n"
        ),
        "tests": [
            "def test_multipliers():\n"
            "    funcs = make_multipliers()\n"
            "    assert [f(5) for f in funcs] == [0, 5, 10]",
        ],
    },
    # D5-008: concurrency race condition
    {
        "id": "L1-D5-PY-008", "difficulty": 4,
        "tags": ["concurrency", "race-condition"],
        "prompt": (
            "The function `increment_counter` in `main.py` is supposed to be "
            "thread-safe, but a race condition causes incorrect counts. "
            "Fix the bug by adding proper synchronization."
        ),
        "buggy_code": (
            "import threading\n\n"
            "counter = 0\n\n"
            "def increment_counter(n: int) -> int:\n"
            "    global counter\n"
            "    counter = 0\n"
            "    def increment():\n"
            "        global counter\n"
            "        for _ in range(n):\n"
            "            counter += 1\n"
            "    threads = [threading.Thread(target=increment) for _ in range(10)]\n"
            "    for t in threads:\n"
            "        t.start()\n"
            "    for t in threads:\n"
            "        t.join()\n"
            "    return counter\n"
        ),
        "tests": [
            "def test_counter():\n"
            "    result = increment_counter(1000)\n"
            "    assert result == 10000",
        ],
    },
    # D5-009: resource leak
    {
        "id": "L1-D5-PY-009", "difficulty": 4,
        "tags": ["resource", "file", "leak"],
        "prompt": (
            "The function `read_file_lines` in `main.py` has a resource leak "
            "and may return wrong results on error. Fix all bugs.\n"
            "It should read and return all lines from a text file."
        ),
        "buggy_code": (
            "def read_file_lines(filepath: str) -> list[str]:\n"
            "    f = open(filepath, 'r')\n"
            "    lines = f.read().split('\\n')\n"
            "    return lines\n"
        ),
        "tests": [
            "def test_read(tmp_path):\n    import os\n"
            "    f = tmp_path / 'test.txt'\n"
            "    f.write_text('line1\\nline2\\nline3')\n"
            "    assert read_file_lines(str(f)) == ['line1', 'line2', 'line3']",
            "def test_empty(tmp_path):\n    import os\n"
            "    f = tmp_path / 'empty.txt'\n"
            "    f.write_text('')\n"
            "    assert read_file_lines(str(f)) == ['']",
            "def test_not_found():\n"
            "    try:\n"
            "        read_file_lines('/nonexistent/file.txt')\n"
            "        assert False, 'should have raised'\n"
            "    except FileNotFoundError:\n"
            "        pass",
        ],
    },
    # D5-010: data corruption
    {
        "id": "L1-D5-PY-010", "difficulty": 5,
        "tags": ["data", "mutation", "side-effect"],
        "prompt": (
            "The function `merge_user_data` in `main.py` has two bugs: "
            "it mutates input data unexpectedly, and duplicates entries. "
            "Find and fix both bugs.\n"
            "It should merge new_data into existing dict without side effects."
        ),
        "buggy_code": (
            "def merge_user_data(existing: dict, new_data: dict) -> dict:\n"
            "    # Bug 1: mutates input\n"
            "    result = existing\n"
            "    for key in new_data:\n"
            "        # Bug 2: overwrites nested dicts incorrectly\n"
            "        if key in result and isinstance(result[key], dict):\n"
            "            result[key] = new_data[key]\n"
            "        else:\n"
            "            result[key] = new_data[key]\n"
            "    return result\n"
        ),
        "tests": [
            "def test_no_mutation():\n"
            "    a = {'x': 1}\n"
            "    b = {'y': 2}\n"
            "    result = merge_user_data(a, b)\n"
            "    assert result == {'x': 1, 'y': 2}\n"
            "    assert a == {'x': 1}, 'input should not be mutated'",
            "def test_nested_merge():\n"
            "    a = {'profile': {'name': 'Alice', 'age': 30}}\n"
            "    b = {'profile': {'name': 'Bob'}}\n"
            "    result = merge_user_data(a, b)\n"
            "    assert result['profile']['name'] == 'Bob'\n"
            "    assert result['profile']['age'] == 30",
            "def test_empty():\n"
            "    assert merge_user_data({}, {'a': 1}) == {'a': 1}",
        ],
    },
]


def main():
    for item in ITEMS:
        item_dir = ITEMS_DIR / item["id"]
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
            "estimated_time_min": item["difficulty"] * 5,
            "tags": item["tags"],
            "sandbox": {
                "image": "python",
                "dependencies": ["pytest"],
                "network": "none",
            },
            "prompt_template": item["prompt"],
            "context_files": ["context/main.py"],
            "expected_artifacts": ["main.py"],
            "scoring": {
                "type": "unit_test",
                "test_command": "python -m pytest judge/test_main.py -v",
                "pass_threshold": 0.85,
            },
            "created": "2026-07-01",
            "version": "1.0",
        }
        (item_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False)
        )
        (context_dir / "main.py").write_text(item["buggy_code"])
        (judge_dir / "test_main.py").write_text(
            "from main import *\n\n\n" + "\n\n\n".join(item["tests"]) + "\n"
        )
        print(f"Created {item['id']} (difficulty {item['difficulty']})")

    # Update registry
    with open(Path(__file__).parent.parent / "test_items" / "registry.json") as f:
        reg = json.load(f)
    for item in ITEMS:
        entry = {"id": item["id"], "path": f"l1/d5_bug_fix/{item['id']}", "enabled": True}
        if entry not in reg["items"]:
            reg["items"].append(entry)
    with open(Path(__file__).parent.parent / "test_items" / "registry.json", "w") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
    print(f"Registry updated: {len(reg['items'])} items total")


if __name__ == "__main__":
    main()
