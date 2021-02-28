from . import queries
from .repositories import AbstractRepository, DataNotFoundError
import asyncio
from sources.data_processing.queries import AbstractQuery, FailedQueryResponse, KeywordQuery
from threading import Timer
from sources.data_processing.async_mp_queue import AsyncMPQueue
import functools
import aiohttp


class TerminationFlag(queries.AbstractQuery):
    """Flag which can be passed into the query_queue to indicate slow
    Termination. (All tasks will be completed first)
    """

    def __init__(self):
        super().__init__(-1)


class TerminationTimeoutFlag(queries.AbstractQuery):
    """Flag which can be passed into the query_queue to indicate Termination.
    It will try to execute all remaining tasks until timeout has passed.
    """

    def __init__(self, timeout=None):
        super().__init__(-1)
        self.timeout = timeout


class AllRepositoriesTriedError(Exception):
    pass


def run_delegator(query_delegation_queue: AsyncMPQueue,
                  response_queue: AsyncMPQueue):
    delegator = QueryDelegator(query_delegation_queue,
                               response_queue)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(delegator.process_queries())
    loop.close()


class QueryCounter:
    """Query Counter is a simple Utility tool that keeps track of the number
    of active requests outgoing on different repositories.
    """
    repo_intervals = {}

    def __init__(self):
        self._active_concurrent_requests = {}
        self._requests_in_last_time_interval = {}

    def register_new_request(self, repo_identifier):
        self._active_concurrent_requests[repo_identifier] = \
            1 + self._active_concurrent_requests.get(repo_identifier, 0)
        self._requests_in_last_time_interval[repo_identifier] = \
            1 + self._requests_in_last_time_interval.get(repo_identifier, 0)

        t = Timer(QueryCounter.repo_intervals[repo_identifier],
                  self.reduce_requests_in_last_interval, args=[repo_identifier])
        t.start()

    def request_completed(self, repo_identifier):
        self._active_concurrent_requests[repo_identifier] -= 1

    def reduce_requests_in_last_interval(self, repo_identifier: str):
        self._requests_in_last_time_interval[repo_identifier] -= 1

    def get_open_connections_for_repo(self, repo_identifier):
        return self._active_concurrent_requests[repo_identifier]

    def get_num_request_last_interval(self, repo_identifier):
        return self._requests_in_last_time_interval[repo_identifier]


class QueryDelegator:

    def __init__(self,
                 query_delegation_queue: AsyncMPQueue,
                 response_queue: AsyncMPQueue):
        self._query_delegation_queue = query_delegation_queue
        self._response_queue = response_queue

    def generate_journal_repo_preferences(self):
        pass
    
    repo_identifier_repo_map = {"openaire", "crossref", "CORE", "arxiv", "ms_academic"}
    query_repository_preferences = {"KeywordQuery" : ["openaire", "CORE", "crossref"],
                                    "JournalQuery" : ["crossref", "openaire", "CORE"]}

    async def choose_repository(self, query) -> AbstractRepository:
        raise AllRepositoriesTriedError

    async def handle_query(self, query: AbstractQuery, session):
        try:
            repo = await self.choose_repository(query)
        except AllRepositoriesTriedError as e:
            self._response_queue.put(
                FailedQueryResponse(query.query_id))
            return

        try:
            result = await repo.execute_query(query, session)
            self._response_queue.put(result)
        except DataNotFoundError as e:
            query.store_scheduling_information(repo.get_identifier())
            self._query_delegation_queue.put(query)

    async def process_queries(self):
        initial_tasks = set(asyncio.all_tasks())
        async with aiohttp.ClientSession() as session:
            while True:
                query: queries.AbstractQuery = await \
                    self._query_delegation_queue.async_get()

                # Check for Termination Signal
                if isinstance(query, type(TerminationFlag)):
                    print("Terminated Loop")
                    timeout = None
                    break
                if isinstance(query, type(TerminationTimeoutFlag)):
                    print("Terminated Loop Forcibly")
                    timeout = query.timeout
                    break

                asyncio.create_task(self.handle_query(query, session))

            await asyncio.wait(asyncio.all_tasks() - initial_tasks,
                               timeout=timeout)
