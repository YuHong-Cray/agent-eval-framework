from main import *


def test_basic():
    assert remove_vowels('hello world') == 'hll wrld'


def test_all_vowels():
    assert remove_vowels('aeiou') == ''


def test_no_vowels():
    assert remove_vowels('rhythm') == 'rhythm'
