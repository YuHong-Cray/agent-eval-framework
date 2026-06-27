from main import parse_json_value


def test_null():
    assert parse_json_value('null') is None


def test_bool():
    assert parse_json_value('true') is True
    assert parse_json_value('false') is False


def test_int():
    assert parse_json_value('42') == 42
    assert parse_json_value('-7') == -7


def test_string():
    assert parse_json_value('"hello"') == "hello"


def test_array():
    assert parse_json_value('[1, 2, 3]') == [1, 2, 3]


def test_object():
    assert parse_json_value('{"a": 1}') == {'a': 1}
