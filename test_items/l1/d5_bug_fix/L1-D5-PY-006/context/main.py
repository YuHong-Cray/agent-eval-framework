def is_palindrome(s: str) -> bool:
    s = s.lower().replace(' ', '')
    for i in range(len(s)):
        if s[i] != s[-i]:  # bug here
            return False
    return True
