import asyncio
import functools
from queue import Queue
from typing import List

class AsyncMTQueue:
    """An implementation of a synchronous queue that provides both interfaces for asyncio and blocking get/puts.
       It does that by wrapping all blocking calls with an executor.
       
       All functions do the same thing as the queue in the standard library.
    """    
    def __init__(self, max_size=0):
        self._queue = Queue(maxsize=max_size)

    async def async_get(self):
        return await asyncio.get_running_loop().run_in_executor(None,
                                                                self.get_blocking)

    def get_blocking(self, timeout=None):
        return self._queue.get(block=True, timeout=timeout)

    def put(self, val, block=True):
        self._queue.put(val, block=block)

    async def async_put(self, val):
        func = functools.partial(self.put, val=val, block=True)
        asyncio.get_running_loop().run_in_executor(None, func)

    def qsize(self):
        return self._queue.qsize()

    def get_nowait(self):
        try:
            return self._queue.get_nowait()
        except Exception as e:
            return None

    def put_nowait(self, val):
        self._queue.put_nowait(val)

    def get(self, block, timeout):
        if block:
            return self.get_blocking(timeout)
        else:
            return self.get_nowait()

    def get_all_available(self) -> List:
        """Helper Method that returns all currently available entries in the internal queue nonblocking.

        Returns:
            List: All elements returned from the internal queue.
        """        
        ls = []
        while True:
            tmp = self.get_nowait()
            if tmp is not None:
                ls.append(tmp)
            else:
                break
        return ls
