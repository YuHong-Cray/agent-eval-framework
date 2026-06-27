from main import reverse_words


def test_basic():
    assert reverse_words("hello world") == "world hello"


def test_single():
    assert reverse_words("hello") == "hello"


def test_empty():
    assert reverse_words("") == ""


def test_three():
    assert reverse_words("a b c") == "c b a"
