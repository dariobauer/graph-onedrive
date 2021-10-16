"""Decorators to wrap functions and methods for testing and debugging.
"""
import tracemalloc
from functools import wraps
from time import perf_counter


def measure_performance(func):
    """TESTING: Measure performance of a function."""

    @wraps(func)
    def wrapper_performance(*args, **kwargs):
        tracemalloc.start()
        start_time = perf_counter()
        wrapped_func = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        finish_time = perf_counter()
        print(f"Function: {func.__name__}")
        print(f"Method: {func.__doc__}")
        print(
            f"Memory usage:\t\t {current / 10**6:.6f} MB \n"
            f"Peak memory usage:\t {peak / 10**6:.6f} MB "
        )
        print(f"Time elapsed is seconds: {finish_time - start_time:.6f}")
        print(f'{"-"*40}')
        tracemalloc.stop()
        return wrapped_func

    return wrapper_performance


def debug(func):
    """DEBUGGING: Print the function signature and return value."""

    @wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]  # 1
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  # 2
        signature = ", ".join(args_repr + kwargs_repr)  # 3
        print(f"Calling {func.__name__}({signature})")
        wrapped_func = func(*args, **kwargs)
        print(f"{func.__name__!r} returned {value!r}")  # 4
        return wrapped_func

    return wrapper_debug
