from main import is_palindrome


def test_basic():
    assert is_palindrome('racecar') is True


def test_not_pal():
    assert is_palindrome('hello') is False


def test_phrase():
    assert is_palindrome('A man, a plan, a canal: Panama') is True


def test_empty():
    assert is_palindrome('') is True
