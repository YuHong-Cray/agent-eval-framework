from main import LRUCache


def test_basic():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1
    c.put(3, 3)
    assert c.get(2) == -1
    c.put(4, 4)
    assert c.get(1) == -1
    assert c.get(3) == 3
    assert c.get(4) == 4


def test_update():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(1, 10)
    assert c.get(1) == 10


def test_not_found():
    c = LRUCache(1)
    assert c.get(99) == -1
