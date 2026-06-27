from main import group_anagrams


def test_basic():
    result = group_anagrams(['eat','tea','tan','ate','nat','bat'])
    expected = [['ate','eat','tea'],['bat'],['nat','tan']]
    assert sorted([sorted(g) for g in result]) == sorted([sorted(g) for g in expected])


def test_empty():
    assert group_anagrams([]) == []


def test_single():
    assert group_anagrams(['hello']) == [['hello']]
