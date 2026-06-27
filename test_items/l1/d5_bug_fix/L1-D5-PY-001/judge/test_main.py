from main import *


def test_nonempty():
    assert sum_list([1, 2, 3, 4, 5]) == 15


def test_empty():
    assert sum_list([]) == 0


def test_single():
    assert sum_list([42]) == 42
