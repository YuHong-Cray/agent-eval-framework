from main import *


def test_counter():
    result = increment_counter(1000)
    assert result == 10000
