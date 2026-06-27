from main import *


def test_basic():
    assert average([1, 2, 3, 4]) == 2.5


def test_integers():
    assert average([1, 2]) == 1.5


def test_empty():
    assert average([]) == 0.0
