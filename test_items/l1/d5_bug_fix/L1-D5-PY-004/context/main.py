def average(items: list[int]) -> float:
    if not items:
        return 0.0
    return sum(items) / len(items)  # bug in Python 2?
