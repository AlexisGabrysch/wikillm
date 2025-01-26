import time

def track_latency(func):
    """Tracks the latency of a function call."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Latency: {end_time - start_time:.2f}s")
        return result
    return wrapper

def guardrail_instance():
    """Returns a guardrail instance for safety."""
    # Placeholder: Implement guardrails
    return True
