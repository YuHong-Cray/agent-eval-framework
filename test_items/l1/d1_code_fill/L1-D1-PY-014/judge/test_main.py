from main import run_in_parallel


def test_basic():
    import time
    def a(): time.sleep(0.1); return 1
    def b(): return 2
    result = run_in_parallel([a, b])
    assert result == [1, 2]


def test_empty():
    assert run_in_parallel([]) == []


def test_single():
    def x(): return 42
    assert run_in_parallel([x]) == [42]
