from multiprocessing import Process
import queue
import typing
from multiprocessing import Process

from sources.data_processing.async_mp_queue import AsyncMPQueue
from sources.data_processing.queries import AbstractQuery, Response
from sources.data_processing.query_delegator import run_delegator, \
    TerminationFlag


class PaperScraper:
    """The PaperScraper class is the public interface of the data processing
    pipeline.

    Creating a PaperScraper object initialises a new process from which the
    queries are going to be processed. Communication happens via
    multiprocessing queues. The paper scraper holds one queue for incoming
    queries and one for outgoing ones. A query object must extend
    AbstractQuery from queries.py."""

    def __init__(self):
        self._delegation_queue: AsyncMPQueue = None
        self._response_queue: AsyncMPQueue = None
        self._process = None  # Use with instead

    def delegate_query(self, query: AbstractQuery):
        self._delegation_queue.put(query)

    def poll_all_responses(self) -> typing.List[Response]:
        responses = []
        while True:
            try:
                tmp = self._response_queue.get_nowait()
                responses.append(tmp)
            except queue.Empty as e:
                break

        return responses

    def poll_response(self, blocking=False, timeout=None) -> Response:
        return self._response_queue.get(block=blocking, timeout=timeout)

    def initialise(self):
        self._delegation_queue: AsyncMPQueue[AbstractQuery] = AsyncMPQueue()
        self._response_queue: AsyncMPQueue[Response] = AsyncMPQueue()
        self._process = Process(target=run_delegator,
                                args=(self._delegation_queue,
                                      self._response_queue),
                                name="paper_scraper_runner")

    def terminate(self):
        self._delegation_queue.put(TerminationFlag())
        self._process.join()
        self._process.close()

    def __enter__(self):
        self.initialise()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()
