from main import *


def test_base():
    assert factorial(0) == 1


def test_pos():
    assert factorial(5) == 120


def test_one():
    assert factorial(1) == 1
