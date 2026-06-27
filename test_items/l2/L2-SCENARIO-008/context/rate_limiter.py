"""Token bucket rate limiter ¡ª implement per requirements."""
import time
import threading

class RateLimiter:
    def __init__(self, capacity: int, refill_rate: float):
        """capacity: max tokens, refill_rate: tokens/second"""
        pass

    def allow(self, key: str) -> bool:
        """Return True if request is allowed."""
        pass

class RateLimitMiddleware:
    """Flask WSGI middleware for per-IP rate limiting."""
    def __init__(self, app, capacity: int = 60, refill_rate: float = 1.0):
        pass

    def __call__(self, environ, start_response):
        pass
