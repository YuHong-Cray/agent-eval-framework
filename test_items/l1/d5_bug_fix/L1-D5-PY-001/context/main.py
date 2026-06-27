def sum_list(items: list[int]) -> int:
    total = 0
    for i in range(len(items) - 1):
        total += items[i]
    return total
