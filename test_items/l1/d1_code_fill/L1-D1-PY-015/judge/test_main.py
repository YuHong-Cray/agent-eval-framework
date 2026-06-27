from main import evaluate_expression


def test_basic():
    assert evaluate_expression("3 + 5") == 8


def test_precedence():
    assert evaluate_expression("3 + 5 * 2") == 13


def test_parentheses():
    assert evaluate_expression("(3 + 5) * 2") == 16


def test_division():
    assert evaluate_expression("7 / 2") == 3


def test_complex():
    assert evaluate_expression("10 + 2 * 6 - 8 / 4") == 20
