from main import *


def test_no_mutation():
    a = {'x': 1}
    b = {'y': 2}
    result = merge_user_data(a, b)
    assert result == {'x': 1, 'y': 2}
    assert a == {'x': 1}, 'input should not be mutated'


def test_nested_merge():
    a = {'profile': {'name': 'Alice', 'age': 30}}
    b = {'profile': {'name': 'Bob'}}
    result = merge_user_data(a, b)
    assert result['profile']['name'] == 'Bob'
    assert result['profile']['age'] == 30


def test_empty():
    assert merge_user_data({}, {'a': 1}) == {'a': 1}
