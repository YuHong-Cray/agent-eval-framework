def remove_vowels(s: str) -> str:
    vowels = 'aeiouAEIOU'
    result = list(s)
    for i, ch in enumerate(result):
        if ch in vowels:
            del result[i]
    return ''.join(result)
