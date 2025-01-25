from random import uniform


def get_expo_backoff(
        attempt_number: int,
        base_delay: int,
        jitter: bool = False,
        max_delay: int = 60
) -> int:
    delay = base_delay * (2 ** (attempt_number - 1))
    delay = min(delay, max_delay)
    jitter = uniform(0, delay) if jitter else 0
    return delay + jitter
