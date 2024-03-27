import datetime
import threading

from pathlib import Path

lock = threading.Lock()


def project_root() -> Path:
    """Returns project root folder."""
    return Path(__file__).parent


def threading_lock(function):
    """Acquires the lock on a function that should be executed by
    only one thread at a time"""
    def wrapper(*args, **kwargs):
        with lock:
            print(f'Lock acquired: {datetime.datetime.now()}')
            result = function(*args, **kwargs)
        print(f'Lock released: {datetime.datetime.now()}')
        return result

    # Proxying all methods of `function` to the external `wrapper`
    # E.g., if the `function` is cached and then wrapped, you can still do wrapper.clear_cache()
    [setattr(wrapper, method, getattr(function, method)) for method in dir(function)
     if callable(getattr(function, method)) and not method.startswith("__")]

    return wrapper


def clean_case_id(case_id: str):
    case_id = case_id.replace('_full', '')
    return case_id
