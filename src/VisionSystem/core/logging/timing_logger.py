import time
from functools import wraps

import psutil


def timing_logger(log_func=None, log_memory_cpu=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            total_time = time.time() - start_time

            msg = f"[Timing] {func.__name__} executed in {total_time*1000:.2f}ms"

            if log_memory_cpu:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
                msg += f" | Memory: {memory_mb:.1f}MB | CPU: {cpu_percent:.1f}%"

            # Call the logger function if provided
            if log_func:
                log_func(msg)
            else:
                print(msg)

            return result
        return wrapper
    return decorator