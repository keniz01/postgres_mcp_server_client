import time
import asyncio
from functools import wraps

class OperationTimer:
    def __init__(self, func):
        self.func = func
        wraps(func)(self)  # Preserve metadata (e.g., __name__, __doc__)

    def __call__(self, *args, **kwargs):
        if asyncio.iscoroutinefunction(self.func):
            @wraps(self.func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                result = await self.func(*args, **kwargs)
                elapsed = time.time() - start_time
                print(f"{self.func.__name__} took {elapsed:.2f} seconds.")
                return result
            return async_wrapper(*args, **kwargs)
