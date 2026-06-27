from main import binary_search


def test_found():
    assert binary_search([1,3,5,7,9], 5) == 2


def test_not_found():
    assert binary_search([1,3,5,7,9], 4) == -1


def test_first():
    assert binary_search([1,2,3], 1) == 0


def test_last():
    assert binary_search([1,2,3], 3) == 2


def test_empty():
    assert binary_search([], 1) == -1
