from main import topological_sort


def test_basic():
    result = topological_sort(4, [(0,1),(0,2),(1,3),(2,3)])
    assert result in ([0,1,2,3], [0,2,1,3])


def test_cycle():
    assert topological_sort(3, [(0,1),(1,2),(2,0)]) == []


def test_single_node():
    assert topological_sort(1, []) == [0]
