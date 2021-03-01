import asyncio
import time

import pytest

from sources.data_processing.async_mp_queue import AsyncMPQueue
from sources.data_processing.queries import AbstractQuery, KeywordQuery
from sources.data_processing.query_delegator import QueryCounter, \
    QueryDelegator, TerminationFlag


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
        delegator = QueryDelegator(AsyncMPQueue(), AsyncMPQueue())

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
        return QueryDelegator(AsyncMPQueue(), AsyncMPQueue())

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

        print(delegator._response_queue.get_nowait())
