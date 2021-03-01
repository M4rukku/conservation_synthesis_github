from multiprocessing import Queue
import asyncio
import functools


class AsyncMPQueue:
    def __init__(self, max_size=0):
        self._queue = Queue(maxsize=max_size)

    async def async_get(self):
        return await asyncio.get_running_loop().run_in_executor(None,
                                                          self.get_blocking)

    def get_blocking(self, timeout = None):
        return self._queue.get(block=True, timeout=timeout)

    def put(self, val, block=True):
        self._queue.put(val, block=block)

    async def async_put(self, val):
        func = functools.partial(self.put, val=val, block=True)
        asyncio.get_running_loop().run_in_executor(None, func)

    def qsize(self):
        return self._queue.qsize()

    def get_nowait(self):
        return self._queue.get_nowait()

    def put_nowait(self, val):
        self._queue.put_nowait(val)

    def get(self, block, timeout):
        if block:
            self.get_blocking(timeout)
        else:
            self.get_nowait()
