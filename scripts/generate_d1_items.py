"""Generate 15 D1 code-fill test items (Python)."""
import json
from pathlib import Path

ITEMS_DIR = Path(__file__).parent.parent / "test_items" / "l1" / "d1_code_fill"

ITEMS = [
    # ── Difficulty 1: 基础 ──
    {
        "id": "L1-D1-PY-001",
        "difficulty": 1,
        "tags": ["string", "basic"],
        "prompt": (
            "Implement `reverse_words(s: str) -> str` in `main.py`.\n"
            "Reverse the order of words separated by single spaces. "
            "Empty input returns empty string.\n"
            'Example: "hello world" -> "world hello"'
        ),
        "stub": "def reverse_words(s: str) -> str:\n    # TODO: implement\n    pass\n",
        "tests": [
            ('def test_basic():\n    assert reverse_words("hello world") == "world hello"'),
            ('def test_single():\n    assert reverse_words("hello") == "hello"'),
            ('def test_empty():\n    assert reverse_words("") == ""'),
            ('def test_three():\n    assert reverse_words("a b c") == "c b a"'),
        ],
    },
    {
        "id": "L1-D1-PY-002",
        "difficulty": 1,
        "tags": ["string", "counting"],
        "prompt": (
            "Implement `count_vowels(s: str) -> int` in `main.py`.\n"
            "Return the number of vowels (a, e, i, o, u) in the string, case-insensitive.\n"
            'Example: "Hello World" -> 3'
        ),
        "stub": "def count_vowels(s: str) -> int:\n    pass\n",
        "tests": [
            ('def test_basic():\n    assert count_vowels("Hello World") == 3'),
            ('def test_all_vowels():\n    assert count_vowels("aeiou") == 5'),
            ('def test_no_vowels():\n    assert count_vowels("rhythm") == 0'),
            ('def test_uppercase():\n    assert count_vowels("AEIOU") == 5'),
        ],
    },
    {
        "id": "L1-D1-PY-003",
        "difficulty": 1,
        "tags": ["math", "iteration"],
        "prompt": (
            "Implement `fibonacci(n: int) -> int` in `main.py`.\n"
            "Return the nth Fibonacci number (0-indexed: fib(0)=0, fib(1)=1).\n"
            "n >= 0, n <= 30. Use iteration."
        ),
        "stub": "def fibonacci(n: int) -> int:\n    pass\n",
        "tests": [
            ("def test_fib0():\n    assert fibonacci(0) == 0"),
            ("def test_fib1():\n    assert fibonacci(1) == 1"),
            ("def test_fib5():\n    assert fibonacci(5) == 5"),
            ("def test_fib10():\n    assert fibonacci(10) == 55"),
        ],
    },
    # ── Difficulty 2 ──
    {
        "id": "L1-D1-PY-004",
        "difficulty": 2,
        "tags": ["list", "merge"],
        "prompt": (
            "Implement `merge_sorted(a: list[int], b: list[int]) -> list[int]` in `main.py`.\n"
            "Merge two already-sorted lists into one sorted list. "
            "Do not use sorted() or .sort(). O(n) time.\n"
            "Example: [1,3,5], [2,4,6] -> [1,2,3,4,5,6]"
        ),
        "stub": "def merge_sorted(a: list[int], b: list[int]) -> list[int]:\n    pass\n",
        "tests": [
            ('def test_equal_size():\n    assert merge_sorted([1,3,5], [2,4,6]) == [1,2,3,4,5,6]'),
            ('def test_one_empty():\n    assert merge_sorted([], [1,2,3]) == [1,2,3]'),
            ('def test_both_empty():\n    assert merge_sorted([], []) == []'),
            ('def test_duplicates():\n    assert merge_sorted([1,2,2], [2,3,3]) == [1,2,2,2,3,3]'),
        ],
    },
    {
        "id": "L1-D1-PY-005",
        "difficulty": 2,
        "tags": ["list", "set"],
        "prompt": (
            "Implement `find_duplicates(items: list[int]) -> list[int]` in `main.py`.\n"
            "Return a sorted list of integers that appear more than once.\n"
            "Example: [1,2,3,2,4,3] -> [2,3]"
        ),
        "stub": "def find_duplicates(items: list[int]) -> list[int]:\n    pass\n",
        "tests": [
            ('def test_basic():\n    assert find_duplicates([1,2,3,2,4,3]) == [2,3]'),
            ('def test_no_dup():\n    assert find_duplicates([1,2,3]) == []'),
            ('def test_all_dup():\n    assert find_duplicates([1,1,1]) == [1]'),
            ('def test_empty():\n    assert find_duplicates([]) == []'),
        ],
    },
    {
        "id": "L1-D1-PY-006",
        "difficulty": 2,
        "tags": ["string", "palindrome"],
        "prompt": (
            "Implement `is_palindrome(s: str) -> bool` in `main.py`.\n"
            "Return True if the string reads the same forward/backward.\n"
            "Ignore case and non-alphanumeric characters.\n"
            "Example: 'A man, a plan, a canal: Panama' -> True"
        ),
        "stub": "def is_palindrome(s: str) -> bool:\n    pass\n",
        "tests": [
            ("def test_basic():\n    assert is_palindrome('racecar') is True"),
            ("def test_not_pal():\n    assert is_palindrome('hello') is False"),
            ("def test_phrase():\n    assert is_palindrome('A man, a plan, a canal: Panama') is True"),
            ("def test_empty():\n    assert is_palindrome('') is True"),
        ],
    },
    # ── Difficulty 3 ──
    {
        "id": "L1-D1-PY-007",
        "difficulty": 3,
        "tags": ["algorithm", "search"],
        "prompt": (
            "Implement `binary_search(arr: list[int], target: int) -> int` in `main.py`.\n"
            "Return the index of target in the sorted list, or -1 if not found.\n"
            "Use O(log n) binary search. Do not use list.index().\n"
            "Example: [1,3,5,7,9], 5 -> 2"
        ),
        "stub": "def binary_search(arr: list[int], target: int) -> int:\n    pass\n",
        "tests": [
            ("def test_found():\n    assert binary_search([1,3,5,7,9], 5) == 2"),
            ("def test_not_found():\n    assert binary_search([1,3,5,7,9], 4) == -1"),
            ("def test_first():\n    assert binary_search([1,2,3], 1) == 0"),
            ("def test_last():\n    assert binary_search([1,2,3], 3) == 2"),
            ("def test_empty():\n    assert binary_search([], 1) == -1"),
        ],
    },
    {
        "id": "L1-D1-PY-008",
        "difficulty": 3,
        "tags": ["recursion", "list"],
        "prompt": (
            "Implement `flatten(nested: list) -> list` in `main.py`.\n"
            "Flatten arbitrarily nested lists into a single flat list.\n"
            "Example: [1, [2, [3, 4]], 5] -> [1,2,3,4,5]"
        ),
        "stub": "def flatten(nested: list) -> list:\n    pass\n",
        "tests": [
            ("def test_basic():\n    assert flatten([1, [2, [3, 4]], 5]) == [1,2,3,4,5]"),
            ("def test_flat():\n    assert flatten([1,2,3]) == [1,2,3]"),
            ("def test_empty():\n    assert flatten([]) == []"),
            ("def test_deep():\n    assert flatten([[[[1]]]]) == [1]"),
        ],
    },
    {
        "id": "L1-D1-PY-009",
        "difficulty": 3,
        "tags": ["string", "hash", "grouping"],
        "prompt": (
            "Implement `group_anagrams(words: list[str]) -> list[list[str]]` in `main.py`.\n"
            "Group words that are anagrams of each other. "
            "Return groups in any order, words within each group sorted alphabetically.\n"
            "Example: ['eat','tea','tan','ate','nat','bat'] -> [['ate','eat','tea'],['bat'],['nat','tan']]"
        ),
        "stub": "def group_anagrams(words: list[str]) -> list[list[str]]:\n    pass\n",
        "tests": [
            ("def test_basic():\n    result = group_anagrams(['eat','tea','tan','ate','nat','bat'])\n"
             "    expected = [['ate','eat','tea'],['bat'],['nat','tan']]\n"
             "    assert sorted([sorted(g) for g in result]) == sorted([sorted(g) for g in expected])"),
            ("def test_empty():\n    assert group_anagrams([]) == []"),
            ("def test_single():\n    assert group_anagrams(['hello']) == [['hello']]"),
        ],
    },
    # ── Difficulty 4 ──
    {
        "id": "L1-D1-PY-010",
        "difficulty": 4,
        "tags": ["data-structure", "cache"],
        "prompt": (
            "Implement an LRU Cache class in `main.py`.\n"
            "`LRUCache(capacity: int)` — initialize with capacity.\n"
            "`get(key: int) -> int` — return value or -1 if not found.\n"
            "`put(key: int, value: int) -> None` — insert/update, evict LRU if full.\n"
            "Both get and put must be O(1)."
        ),
        "stub": (
            "class LRUCache:\n"
            "    def __init__(self, capacity: int):\n"
            "        pass\n"
            "    def get(self, key: int) -> int:\n"
            "        pass\n"
            "    def put(self, key: int, value: int) -> None:\n"
            "        pass\n"
        ),
        "tests": [
            ("def test_basic():\n    c = LRUCache(2)\n    c.put(1, 1)\n    c.put(2, 2)\n"
             "    assert c.get(1) == 1\n    c.put(3, 3)\n    assert c.get(2) == -1\n"
             "    c.put(4, 4)\n    assert c.get(1) == -1\n    assert c.get(3) == 3\n    assert c.get(4) == 4"),
            ("def test_update():\n    c = LRUCache(2)\n    c.put(1, 1)\n    c.put(1, 10)\n"
             "    assert c.get(1) == 10"),
            ("def test_not_found():\n    c = LRUCache(1)\n    assert c.get(99) == -1"),
        ],
    },
    {
        "id": "L1-D1-PY-011",
        "difficulty": 4,
        "tags": ["parsing", "string"],
        "prompt": (
            "Implement `parse_json_value(s: str) -> Any` in `main.py`.\n"
            "Parse a simplified JSON value: null, bool (true/false), integer, "
            "string (double-quoted with \\\\ escapes for \\\" and \\\\), "
            "array ([...]), or object ({...}). Keys are always double-quoted strings.\n"
            "Do NOT use json.loads(). Return the parsed Python object.\n"
            'Example: \'{"a": 1, "b": [2, "hello"]}\' -> {"a": 1, "b": [2, "hello"]}'
        ),
        "stub": "def parse_json_value(s: str) -> object:\n    pass\n",
        "tests": [
            ("def test_null():\n    assert parse_json_value('null') is None"),
            ("def test_bool():\n    assert parse_json_value('true') is True\n    assert parse_json_value('false') is False"),
            ("def test_int():\n    assert parse_json_value('42') == 42\n    assert parse_json_value('-7') == -7"),
            ('def test_string():\n    assert parse_json_value(\'"hello"\') == "hello"'),
            ("def test_array():\n    assert parse_json_value('[1, 2, 3]') == [1, 2, 3]"),
            ("def test_object():\n    assert parse_json_value('{\"a\": 1}') == {'a': 1}"),
        ],
    },
    {
        "id": "L1-D1-PY-012",
        "difficulty": 4,
        "tags": ["algorithm", "dp"],
        "prompt": (
            "Implement `longest_common_subsequence(a: str, b: str) -> int` in `main.py`.\n"
            "Return the length of the longest common subsequence between two strings.\n"
            "A subsequence does not need to be contiguous. Use dynamic programming.\n"
            'Example: "abcde", "ace" -> 3 ("ace" is the LCS)'
        ),
        "stub": "def longest_common_subsequence(a: str, b: str) -> int:\n    pass\n",
        "tests": [
            ('def test_basic():\n    assert longest_common_subsequence("abcde", "ace") == 3'),
            ('def test_no_common():\n    assert longest_common_subsequence("abc", "def") == 0'),
            ('def test_empty():\n    assert longest_common_subsequence("", "abc") == 0'),
            ('def test_full_match():\n    assert longest_common_subsequence("abc", "abc") == 3'),
        ],
    },
    # ── Difficulty 5 ──
    {
        "id": "L1-D1-PY-013",
        "difficulty": 5,
        "tags": ["algorithm", "graph"],
        "prompt": (
            "Implement `topological_sort(n: int, edges: list[tuple[int,int]]) -> list[int]` in `main.py`.\n"
            "Given n nodes (0..n-1) and directed edges (u,v), return a topological order.\n"
            "If no valid order exists (cycle), return empty list. Use Kahn's algorithm.\n"
            "Example: n=4, edges=[(0,1),(0,2),(1,3),(2,3)] -> [0,1,2,3] (or [0,2,1,3])"
        ),
        "stub": (
            "def topological_sort(n: int, edges: list[tuple[int,int]]) -> list[int]:\n    pass\n"
        ),
        "tests": [
            ("def test_basic():\n    result = topological_sort(4, [(0,1),(0,2),(1,3),(2,3)])\n"
             "    assert result in ([0,1,2,3], [0,2,1,3])"),
            ("def test_cycle():\n    assert topological_sort(3, [(0,1),(1,2),(2,0)]) == []"),
            ("def test_single_node():\n    assert topological_sort(1, []) == [0]"),
        ],
    },
    {
        "id": "L1-D1-PY-014",
        "difficulty": 5,
        "tags": ["concurrency", "threading"],
        "prompt": (
            "Implement `run_in_parallel(funcs: list[callable]) -> list` in `main.py`.\n"
            "Execute all given callables in parallel using threads, "
            "collect and return their return values in the same order.\n"
            "Use only the `threading` module. Each callable takes no arguments."
        ),
        "stub": (
            "def run_in_parallel(funcs: list) -> list:\n"
            "    # Use threading to run funcs in parallel\n"
            "    pass\n"
        ),
        "tests": [
            ("def test_basic():\n    import time\n"
             "    def a(): time.sleep(0.1); return 1\n"
             "    def b(): return 2\n"
             "    result = run_in_parallel([a, b])\n"
             "    assert result == [1, 2]"),
            ("def test_empty():\n    assert run_in_parallel([]) == []"),
            ("def test_single():\n    def x(): return 42\n"
             "    assert run_in_parallel([x]) == [42]"),
        ],
    },
    {
        "id": "L1-D1-PY-015",
        "difficulty": 5,
        "tags": ["algorithm", "parsing"],
        "prompt": (
            "Implement `evaluate_expression(expr: str) -> int` in `main.py`.\n"
            "Evaluate a string arithmetic expression containing +, -, *, /, "
            "parentheses, and non-negative integers. Follow standard precedence (*/ before +-).\n"
            "Integer division truncates toward zero. Do not use eval().\n"
            'Example: "3 + 5 * 2" -> 13'
        ),
        "stub": "def evaluate_expression(expr: str) -> int:\n    pass\n",
        "tests": [
            ('def test_basic():\n    assert evaluate_expression("3 + 5") == 8'),
            ('def test_precedence():\n    assert evaluate_expression("3 + 5 * 2") == 13'),
            ('def test_parentheses():\n    assert evaluate_expression("(3 + 5) * 2") == 16'),
            ('def test_division():\n    assert evaluate_expression("7 / 2") == 3'),
            ('def test_complex():\n    assert evaluate_expression("10 + 2 * 6 - 8 / 4") == 20'),
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

        # metadata.json
        metadata = {
            "id": item["id"],
            "layer": "L1",
            "dimensions": ["D1"],
            "sub_dimensions": [],
            "language": "python",
            "difficulty": item["difficulty"],
            "estimated_time_min": max(2, item["difficulty"] * 3),
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

        # context/main.py
        (context_dir / "main.py").write_text(item["stub"])

        # judge/test_main.py
        imports = []
        # Extract needed imports from stub
        if "LRUCache" in item["stub"]:
            imports.append("from main import LRUCache")
        elif "class" not in item["stub"]:
            func_name = item["stub"].split("(")[0].replace("def ", "").strip()
            imports.append(f"from main import {func_name}")

        test_content = "\n".join(imports) + "\n\n\n" + "\n\n\n".join(item["tests"]) + "\n"
        (judge_dir / "test_main.py").write_text(test_content)

        print(f"Created {item['id']} (difficulty {item['difficulty']})")

    # Update registry.json
    registry_path = ITEMS_DIR.parent.parent.parent / "registry.json"
    with open(registry_path) as f:
        registry = json.load(f)

    for item in ITEMS:
        entry = {
            "id": item["id"],
            "path": f"l1/d1_code_fill/{item['id']}",
            "enabled": True,
        }
        if entry not in registry["items"]:
            registry["items"].append(entry)

    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"\nUpdated registry.json with {len(ITEMS)} items total")


if __name__ == "__main__":
    main()
