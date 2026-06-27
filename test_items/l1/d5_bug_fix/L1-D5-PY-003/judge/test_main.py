from main import *


def test_single_call():
    assert add_item('a') == ['a']


def test_multiple_calls_independent():
    r1 = add_item('a')
    r2 = add_item('b')
    assert r1 == ['a']
    assert r2 == ['b']
