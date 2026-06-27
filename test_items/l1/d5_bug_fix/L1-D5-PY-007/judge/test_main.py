from main import *


def test_multipliers():
    funcs = make_multipliers()
    assert [f(5) for f in funcs] == [0, 5, 10]
