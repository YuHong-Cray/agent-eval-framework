from main import count_vowels


def test_basic():
    assert count_vowels("Hello World") == 3


def test_all_vowels():
    assert count_vowels("aeiou") == 5


def test_no_vowels():
    assert count_vowels("rhythm") == 0


def test_uppercase():
    assert count_vowels("AEIOU") == 5
