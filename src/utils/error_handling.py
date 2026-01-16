import functools
import logging
from typing import Callable, Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

def safe_execute(default_return: Any = None) -> Callable:
    """Decorator to catch exceptions and return a default value."""
    def decorator(func: Callable[..., T]) -> Callable[..., T | Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T | Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                return default_return
        return wrapper
    return decorator
