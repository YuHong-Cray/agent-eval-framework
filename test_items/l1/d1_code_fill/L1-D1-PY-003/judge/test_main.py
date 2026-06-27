from main import fibonacci


def test_fib0():
    assert fibonacci(0) == 0


def test_fib1():
    assert fibonacci(1) == 1


def test_fib5():
    assert fibonacci(5) == 5


def test_fib10():
    assert fibonacci(10) == 55
