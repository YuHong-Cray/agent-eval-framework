from main import longest_common_subsequence


def test_basic():
    assert longest_common_subsequence("abcde", "ace") == 3


def test_no_common():
    assert longest_common_subsequence("abc", "def") == 0


def test_empty():
    assert longest_common_subsequence("", "abc") == 0


def test_full_match():
    assert longest_common_subsequence("abc", "abc") == 3
