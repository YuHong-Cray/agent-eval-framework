from main import *


def test_pal():
    assert is_palindrome('racecar') is True


def test_not_pal():
    assert is_palindrome('hello') is False


def test_pal_spaces():
    assert is_palindrome('a man a plan a canal panama') is True
