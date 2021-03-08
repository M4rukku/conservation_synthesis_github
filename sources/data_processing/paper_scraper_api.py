import typing
from typing import Optional, List
from threading import Thread

from sources.data_processing.async_mt_queue import AsyncMTQueue
from sources.data_processing.queries import AbstractQuery, Response
from sources.data_processing.query_delegator import run_delegator, \
    TerminationFlag


class PaperScraper:
    """The PaperScraper class is the public interface of the data processing
    ... pipeline.

    Creating a PaperScraper object initialises a new thread from which the
    ...queries are going to be processed. Communication happens via
    ...threadsafe AsyncMTQueue queues. The paper scraper holds one queue for incoming
    ...queries and one for outgoing ones. A query object must extend
    ...AbstractQuery from queries.py.
    
    The PaperScraper keeps track of all delegated queries via their ids and the outgoing responses. 
    ...If all queries have been handled the processed_all_queries attribute will become True.
    
    Note:
        Must be used in combination with the context pattern.
    """

    def __init__(self):
        self._processed_all_queries = True
        self._all_query_ids = set()

        self._delegation_queue: Optional[AsyncMTQueue] = None
        self._response_queue: Optional[AsyncMTQueue] = None
        self._thread = None  # Use with instead

    def delegate_query(self, query: AbstractQuery):
        """Delegates a  query to be handled by the Paperscraper.

        Args:
            query (AbstractQuery): The query to delegate.
        """        
        # potential race, but not a  problem here
        self._processed_all_queries = False
        self._all_query_ids.add(query.query_id)
        self._delegation_queue.put(query)

    def poll_all_available_responses(self) -> typing.List[Response]:
        """Returns all currently available (nonblockingly) responses on the response queue.

        Returns:
            typing.List[Response]: All available responses.
        """        
        responses = self._response_queue.get_all_available()
        self._all_query_ids = self._all_query_ids - \
                              {response.query_id for response in responses}
        return responses

    def poll_response(self, blocking=True, timeout=None) -> Response:
        """[summary]

        Args:
            blocking (bool, optional): Whether the polling should be blocking. Defaults to True.
            timeout (float, optional): Whether the polling should have a timeout. Defaults to None.

        Raises:
            TimeoutError: If get exceeds timeout.
            
        Returns:
            Response: Returns a response object once it is available
        """        
        response: Response = self._response_queue.get(block=blocking, timeout=timeout)
        self._all_query_ids.remove(response.query_id)
        return response

    def initialise(self):
        self._delegation_queue: AsyncMTQueue = AsyncMTQueue()
        self._response_queue: AsyncMTQueue = AsyncMTQueue()
        self._thread = Thread(target=run_delegator,
                              args=(self._delegation_queue,
                                    self._response_queue),
                              name="paper_scraper_runner")
        self._thread.start()

    def delegation_qsize(self):
        return self._delegation_queue.qsize()

    @property
    def processed_all_queries(self):
        """Returns true iff all delegated queries have returned a response object that has been processed.

        Returns:
            bool: Have all queries been processed?
        """        
        if len(self._all_query_ids)==0:
            self._processed_all_queries = True

        return self._processed_all_queries

    def terminate(self):
        self._delegation_queue.put(TerminationFlag())
        self._thread.join()

    def __enter__(self):
        self.initialise()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()
