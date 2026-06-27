from main import merge_sorted


def test_equal_size():
    assert merge_sorted([1,3,5], [2,4,6]) == [1,2,3,4,5,6]


def test_one_empty():
    assert merge_sorted([], [1,2,3]) == [1,2,3]


def test_both_empty():
    assert merge_sorted([], []) == []


def test_duplicates():
    assert merge_sorted([1,2,2], [2,3,3]) == [1,2,2,2,3,3]
