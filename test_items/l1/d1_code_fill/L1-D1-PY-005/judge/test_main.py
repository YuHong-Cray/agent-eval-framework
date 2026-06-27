from main import find_duplicates


def test_basic():
    assert find_duplicates([1,2,3,2,4,3]) == [2,3]


def test_no_dup():
    assert find_duplicates([1,2,3]) == []


def test_all_dup():
    assert find_duplicates([1,1,1]) == [1]


def test_empty():
    assert find_duplicates([]) == []
