import asyncio
from collections import defaultdict
from threading import Timer

import aiohttp

from sources.data_processing.async_mt_queue import AsyncMTQueue
from sources.data_processing.queries import AbstractQuery, FailedQueryResponse, \
    DoiQuery, KeywordQuery
from . import queries
from .abstract_webscraping import async_get_abstract_from_doi
from .repositories import AbstractRepository, DataNotFoundError, \
    OpenAireRepository, CrossrefRepository, CoreRepository


def valid(field:str):
    return field is not None and field != ""

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
    """Exception that will be raised once we have tried all potential repositories for a given query (and query type).
    """    
    pass


def run_delegator(query_delegation_queue: AsyncMTQueue,
                  response_queue: AsyncMTQueue):
    """The interface to the QueryDelegator. It should called in a new background thread that is running the delegator.

    Args:
        query_delegation_queue (AsyncMTQueue): the queue from which queries will be fetched.
        response_queue (AsyncMTQueue): The queue on which the delegator passes the Response objects.
    """    
    delegator = QueryDelegator(query_delegation_queue,
                               response_queue)
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.run_until_complete(delegator.process_queries())
    try:
        event_loop.close()
    except Exception:
        pass


class QueryCounter:
    """Query Counter is a simple Utility tool that keeps track of the number
    of active requests outgoing on different repositories.
    """
    repo_intervals = defaultdict(lambda: 1)  # WRONG

    def __init__(self):
        self._active_concurrent_requests = defaultdict(lambda: 0)
        self._requests_in_last_time_interval = defaultdict(lambda: 0)

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
    """The QueryDelegator takes queries by waiting on the _query_delegation_queue and executes them by delegating them to appropriate repositories.
        Once a request has been processed, it will be pushed to the _response_queue from which it can be popped.
        Once a TerminationFlag has been pushed, the machine will try to exit.
    """    

    def __init__(self,
                 query_delegation_queue: AsyncMTQueue,
                 response_queue: AsyncMTQueue):
        self._query_delegation_queue = query_delegation_queue
        self._response_queue = response_queue
        self._query_counter = QueryCounter()
        self._terminated = False

    def generate_journal_repo_preferences(self):
        pass

    repo_identifier_repo_map = {"openaire": OpenAireRepository,
                                "crossref": CrossrefRepository,
                                "CORE": CoreRepository}

    repo_identifier_max_conn = {"openaire": 15,
                                "crossref": 12,
                                "CORE": 15}

    query_repository_preferences = \
        {"KeywordQuery": ["openaire", "CORE", "crossref"],
         "DOIQuery": ["openaire", "CORE"],
         "JournalTimeIntervalQuery": ["crossref"]}

    async def wait_until_repository_available(self, repo_identifier):
        """If there are API restricitons on the amount of queries per second on a repository, this is
            function will ensure that these restrictions are met by waiting on the internal QueryCounter.

        Args:
            repo_identifier (str): [description]
        """        
        while (self._query_counter.get_open_connections_for_repo(
                repo_identifier) > self.repo_identifier_max_conn[
                   repo_identifier]
                or
                self._query_counter.get_num_request_last_interval(repo_identifier)>
                self.repo_identifier_max_conn[repo_identifier]):
            await asyncio.sleep(0.5)

    # Version!

    async def choose_repository(self, query) -> AbstractRepository:
        """Selects the appropriate repository for a given query by checking both the query type and the query history.

        Args:
            query (AbstractQuery): The query to process.

        Raises:
            AllRepositoriesTriedError: Raises AllRepositoriesTriedError, if there is no queryable repo left.

        Returns:
            AbstractRepository: The repo to query next.
        """        
        if isinstance(query, queries.KeywordQuery):
            rep_pref = self.query_repository_preferences["KeywordQuery"]
        elif isinstance(query, queries.ISSNTimeIntervalQuery):
            rep_pref = self.query_repository_preferences[
                "JournalTimeIntervalQuery"]
        elif isinstance(query, queries.DoiQuery):
            rep_pref = self.query_repository_preferences["DOIQuery"]
        else:
            raise Exception("Unknown Query Type")

        scheduling_info = query.get_scheduling_information()
        possible_repositories = [repo for repo in rep_pref
                                 if repo not in scheduling_info]
        if len(possible_repositories) == 0:
            raise AllRepositoriesTriedError()

        repo = possible_repositories[0]
        await self.wait_until_repository_available(repo)
        self._query_counter.register_new_request(repo)
        query.store_scheduling_information(repo)

        return self.repo_identifier_repo_map[repo]()

    async def handle_query(self, query: AbstractQuery, session):
        """Asynchronous execution context that performs the query. If unsuccessful, it will update the scheduling
            information on the query and then reissue the query.

        Args:
            query (AbstractQuery): The query to process.
            session ([type]): The Aiohttp client session to use.
        """        
        try:
            repo = await self.choose_repository(query)
        except AllRepositoriesTriedError as e:
            self._response_queue.put(
                FailedQueryResponse(query.query_id))
            return

        try:
            result = await repo.execute_query(query, session)
            self._query_counter.request_completed(repo.get_identifier())

            if isinstance(query, DoiQuery) or isinstance(query, KeywordQuery):
                result.add_journal_data(query.get_journal_data())

                if not valid(result.metadata.abstract):
                    try:
                        result.metadata.abstract = \
                            await async_get_abstract_from_doi(result.metadata.doi)
                    except Exception as e:
                        pass
                self._response_queue.put(result)
            else:
                self._response_queue.put(result)

        except DataNotFoundError as e:
            self._query_delegation_queue.put(query)
            self._query_counter.request_completed(repo.get_identifier())
        except Exception as e:
            self._query_delegation_queue.put(query)
            self._query_counter.request_completed(repo.get_identifier())

    async def process_queries(self):
        """The "run" method of the QueryDelegator. Waits on the delegation queue and schedules all requests to be done. 
            Once a TerminationFlag has been passed, it will try to terminate the process.
        """        
        initial_tasks = set(asyncio.all_tasks())
        async with aiohttp.ClientSession() as session:
            while not self._terminated:
                query: queries.AbstractQuery = await \
                    self._query_delegation_queue.async_get()

                # Check for Termination Signal
                if isinstance(query, TerminationFlag):
                    timeout = None
                    self._terminated = True
                    if len(asyncio.all_tasks() - initial_tasks) > 0:
                        await asyncio.gather(*(asyncio.all_tasks() -
                                               initial_tasks))
                    if self._query_delegation_queue.qsize() == 0:
                        break

                    self._query_delegation_queue.put(TerminationFlag())
                    self._terminated = False
                    continue
                if isinstance(query, TerminationTimeoutFlag):
                    timeout = query.timeout
                    break

                asyncio.create_task(self.handle_query(query, session))

            if len(asyncio.all_tasks() - initial_tasks) > 0:
                await asyncio.wait(asyncio.all_tasks() - initial_tasks,
                                   timeout=timeout)
