import time
import functools
from typing import Callable, Optional, Any
from ..config.settings import RETRY_ATTEMPTS, RETRY_DELAY

def with_retry(max_attempts: Optional[int] = None, delay: Optional[int] = None) -> Callable:
    """
    Decorator to retry a function on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds
    
    Returns:
        Decorated function with retry logic
    """
    max_attempts = max_attempts or RETRY_ATTEMPTS
    delay = delay or RETRY_DELAY
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise
                    
                    # Log the retry attempt
                    print(f"Retry attempt {attempts}/{max_attempts} after error: {str(e)}")
                    
                    # Wait before retrying
                    time.sleep(delay)
            
            # This should never be reached due to the raise in the except block
            raise RuntimeError("Unexpected error in retry logic")
        
        return wrapper
    
    return decorator