import asyncio
import threading
import time

import pytest

from sources.data_processing.async_mp_queue import AsyncMTQueue
from sources.data_processing.queries import AbstractQuery, KeywordQuery, \
    FailedQueryResponse, Response, DoiQuery
from sources.data_processing.query_delegator import QueryCounter, \
    QueryDelegator, TerminationFlag, run_delegator
from sources.data_processing.repositories import strings_approx_equal


class TestCounter:
    @pytest.fixture
    def mock_repo_interval_metadata(self):
        return {"repoA": 1, "repoB": 1, "repoC": 2}

    @pytest.fixture
    def sample_queries(self):
        return ["repoA"] * 3 + ["repoB"] * 5 + ["repoC"] * 1

    @pytest.fixture
    def mock_query_counter(self, mock_repo_interval_metadata):
        qc = QueryCounter()
        QueryCounter.repo_intervals = mock_repo_interval_metadata
        return qc

    def test_num_events_counted_correctly(
            self, mock_query_counter, sample_queries
    ):
        for repo in sample_queries:
            mock_query_counter.register_new_request(repo)
        assert mock_query_counter.get_open_connections_for_repo("repoA") == 3
        assert mock_query_counter.get_open_connections_for_repo("repoB") == 5
        assert mock_query_counter.get_open_connections_for_repo("repoC") == 1
        assert mock_query_counter.get_num_request_last_interval("repoA") == 3
        assert mock_query_counter.get_num_request_last_interval("repoB") == 5
        assert mock_query_counter.get_num_request_last_interval("repoC") == 1

    def test_num_events_reduces(self, mock_query_counter, sample_queries):
        for repo in sample_queries:
            mock_query_counter.register_new_request(repo)
        time.sleep(2)
        assert mock_query_counter.get_num_request_last_interval("repoA") == 0

    def test_interval_counter_is_correct(
            self, mock_query_counter, sample_queries
    ):
        for repo in sample_queries:
            mock_query_counter.register_new_request(repo)
        time.sleep(0.9)
        assert mock_query_counter.get_num_request_last_interval("repoA") == 3
        time.sleep(0.2)
        assert mock_query_counter.get_num_request_last_interval("repoA") == 0

    def test_interval_count_does_not_affect_open_connections(
            self, mock_query_counter, sample_queries
    ):
        for repo in sample_queries:
            mock_query_counter.register_new_request(repo)
        time.sleep(2)
        assert mock_query_counter.get_open_connections_for_repo("repoA") == 3


class TestDelegator:
    class MockEmptyQuery(AbstractQuery):
        def __init__(self):
            super().__init__(-1)

    @pytest.fixture
    def mock_empty_handler_delegator(self):
        delegator = QueryDelegator(AsyncMTQueue(), AsyncMTQueue())

        async def mock_handler(q, s):
            await asyncio.sleep(5)

        delegator.handle_query = mock_handler
        return delegator

    @pytest.fixture
    def terminating_input(self):
        return [TestDelegator.MockEmptyQuery(),
                TestDelegator.MockEmptyQuery(),
                TestDelegator.MockEmptyQuery(),
                TerminationFlag()
                ]

    def test_delegator_terminates(self, mock_empty_handler_delegator,
                                  terminating_input, event_loop):
        delegator = mock_empty_handler_delegator
        for input in terminating_input:
            delegator._query_delegation_queue.put(input)

        event_loop.run_until_complete(delegator.process_queries())

    @pytest.fixture
    def real_delegator(self):
        return QueryDelegator(AsyncMTQueue(), AsyncMTQueue())

    @pytest.fixture
    def sample_query(self):
        return \
            [KeywordQuery(
                1,
                authors=["H. John", "B. Birk"],
                title=r"Ecological palaeoecology and conservation biology: controversies, challenges, and compromises",
                journal_name=None,
                doi="10.1080/21513732.2012.701667",
                start_date=None,
                end_date=None,
            ),
                TerminationFlag()]

    def test_delegator_returns_response(self, real_delegator, sample_query,
                                        event_loop):
        delegator = real_delegator
        query = sample_query

        for input in sample_query:
            delegator._query_delegation_queue.put(input)

        event_loop.run_until_complete(delegator.process_queries())

        assert isinstance(delegator._response_queue.get_nowait(), Response)

    @pytest.fixture
    def failing_kw_query(self):
        return [KeywordQuery(2, doi="3297", title="Algae growth by shading"),
                TerminationFlag()]

    def test_delegator_failing_query(self, real_delegator, failing_kw_query,
                                     event_loop):
        delegator = real_delegator
        query = failing_kw_query

        for ip in failing_kw_query:
            delegator._query_delegation_queue.put(ip)

        event_loop.run_until_complete(delegator.process_queries())

        assert isinstance(delegator._response_queue.get_nowait(),
                          FailedQueryResponse)

    def test_multithreaded(self, sample_query, event_loop):

        query = sample_query
        del_q = AsyncMTQueue()
        resp_q = AsyncMTQueue()

        def run_in_delegator(loop, del_qu, resp_qu):
            delegator = QueryDelegator(del_qu, resp_qu)
            # asyncio.set_event_loop(loop)
            loop = asyncio.new_event_loop()
            loop.run_until_complete(delegator.process_queries())
            loop.close()

        lp = asyncio.get_event_loop()
        thread = threading.Thread(target=run_in_delegator, args=(lp, del_q,
                                                                 resp_q))
        thread.start()
        for ip in query:
            del_q.put(ip)
        thread.join()

        assert isinstance(resp_q.get_nowait(), Response)

    def test_run_delegator(self, sample_query):
        del_q = AsyncMTQueue()
        resp_q = AsyncMTQueue()
        thread = threading.Thread(target=run_delegator,
                                  args=(del_q, resp_q))
        thread.start()
        for ip in sample_query:
            del_q.put(ip)
        thread.join()
        assert isinstance(resp_q.get_nowait(), Response)

    @pytest.fixture
    def list_doi_title(self):
        return [
            (
                "10.1111/rec.12476",  # "1061-2971",
                "Vegetation structure, species life span, and exotic status elucidate plant succession in a limestone quarry reclamation",
            ),
            (
                "10.1111/1365-2664.13471",  # "0021-8901",
                "Combined effects of grazing management and climate on semi-arid steppes: Hysteresis dynamics prevent recovery of degraded rangelands",
            ),
            (
                "10.1111/1365-2664.13315",
                "Conventional methods for enhancing connectivity in conservation planning do not always maintain gene flow",
            ),
            (
                "10.1007/s12237-014-9789-2",
                "Trapping of Rhizophora mangle Propagules by Coexisting Early Successional Species",
            ),
        ]

    def test_delegator_multiple_queries(self, list_doi_title, sample_query):
        del_q = AsyncMTQueue()
        resp_q = AsyncMTQueue()
        thread = threading.Thread(target=run_delegator,
                                  args=(del_q, resp_q))
        thread.start()
        c = 1

        def cnt():
            nonlocal c
            c = c + 1
            return c

        qu = [DoiQuery(cnt(), doi) for doi, title in list_doi_title]
        for q in qu:
            del_q.put(q)
        for ip in sample_query:
            del_q.put(ip)

        thread.join()

        responses = resp_q.get_all_available()
        responses.sort(key=lambda x: x.query_id)

        assert len(responses) == 5
        for i in range(1, 5):
            assert strings_approx_equal(responses[i].metadata.title,
                                        list_doi_title[i-1][1])

class TestBugs:

    @pytest.fixture
    def weird_doi_query(self):
        return [DoiQuery(0, '10.1016/s0929-1393(16)30034-8'),
                TerminationFlag()]

    @pytest.fixture
    def real_delegator(self):
        return QueryDelegator(AsyncMTQueue(), AsyncMTQueue())

    def test_failing_query(self,
                           event_loop,
                           real_delegator,
                           weird_doi_query):

        delegator = real_delegator
        query = weird_doi_query

        for ip in weird_doi_query:
            delegator._query_delegation_queue.put(ip)

        event_loop.run_until_complete(delegator.process_queries())