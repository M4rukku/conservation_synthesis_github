import asyncio
from datetime import date

import aiohttp
import pytest

from sources.data_processing import queries, repositories
from sources.data_processing.queries import KeywordQuery, \
    ISSNTimeIntervalQuery
from sources.data_processing.repositories import (
    OpenAireRepository,
    DataNotFoundError,
    CrossrefRepository,
)


class TestCrossref:
    @pytest.fixture
    def kw_query(self):  # has doi doi="10.1080/21513732.2012.701667"
        return KeywordQuery(
            1,
            authors=[
                "H. John",
                "B. Birks",
            ],  # TODO Authors are wrongly formatted at some parts!
            title=r"Ecological palaeoecology and conservation biology: controversies, challenges, and compromises",
            journal_name=None,
            start_date=None,
            end_date=None,
        )

    @pytest.fixture
    def crossref_repo(self):
        return CrossrefRepository()

    @pytest.fixture
    def failing_query(self):
        return "10.1002/0470441559.ch1", "nonsense"

    @pytest.fixture
    def failing_kw_query(self):
        return KeywordQuery(1, title="Algae growth by shading")

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

    def test_failing_doi_query(self, event_loop, failing_query, crossref_repo):
        with pytest.raises(DataNotFoundError):
            event_loop.run_until_complete(
                crossref_repo.execute_query(
                    queries.DoiQuery(1, failing_query[0])
                )
            )

    def test_failing_kw_query(
            self, event_loop, failing_kw_query, crossref_repo
    ):
        with pytest.raises(DataNotFoundError):
            event_loop.run_until_complete(
                crossref_repo.execute_query(failing_kw_query)
            )

    def test_doi_query(self, event_loop, list_doi_title, crossref_repo):
        awaitables = [
            crossref_repo.execute_query(queries.DoiQuery(1, doi))
            for doi, title in list_doi_title
        ]
        responses = event_loop.run_until_complete(asyncio.gather(*awaitables))

        for response, (doi, title) in zip(responses, list_doi_title):
            assert (
                    repositories.strings_approx_equal(
                        response.metadata.title, title
                    )
                    == True
            )

    def test_kw_query(self, event_loop, kw_query, crossref_repo):
        response = event_loop.run_until_complete(
            crossref_repo.execute_query(kw_query)
        )
        assert response.metadata.doi == "10.1080/21513732.2012.701667"

    ##### Test Journal Time INterval Query
    @pytest.fixture
    def sample_journal_query(self):
        return ISSNTimeIntervalQuery(0,
                                    "1420 - 9101",
                                     date(2018, 1, 1),
                                     date(2019, 1, 1),
                                    )

    def test_query_has_correct_response(self, event_loop,
                                        sample_journal_query,
                                        crossref_repo):
        response = event_loop.run_until_complete(
            crossref_repo.execute_query(sample_journal_query)
        )
        assert len(response.all_articles) == 22


class TestOpenAire:
    # Fixtures
    ############################################################
    @pytest.fixture
    def sample_query(self):
        return KeywordQuery(
            1,
            authors=[
                "H. John",
                "B. Birks",
            ],  # TODO Authors are wrongly formatted at some parts!
            title=r"Ecological palaeoecology and conservation biology: controversies, challenges, and compromises",
            journal_name=None,
            doi="10.1080/21513732.2012.701667",
            start_date=None,
            end_date=None,
        )

    @pytest.fixture
    def failing_query(self):
        return "10.1002/0470441559.ch1", "nonsense"

    @pytest.fixture
    def oa_repo(self):
        return OpenAireRepository()

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

    @pytest.fixture
    def title_that_does_not_exist_query(self):
        return KeywordQuery(1, title="Algae growth by shading")

    # Tests
    ######################################
    async def wrap_with_session(self, query, repo):
        async with aiohttp.ClientSession() as session:
            answer = await repo.execute_query(query, session)
        return answer

    def test_query_dict_is_correctly_formatted(self, oa_repo, sample_query):
        assert oa_repo._get_oa_query_dict_from_keyword_query(sample_query) == {
            "author": "John Birks",
            "doi": "10.1080/21513732.2012.701667",
            "title": "Ecological palaeoecology and conservation biology: controversies, challenges, and compromises",
            "format": "json",
            "size": "5",
        }

    def test_sample_keyword_query(self, event_loop, sample_query, oa_repo):
        response = event_loop.run_until_complete(
            self.wrap_with_session(sample_query, oa_repo)
        )
        print(response.metadata)

        assert (
                response.metadata.title
                == "Ecological palaeoecology and conservation biology: controversies, challenges, and compromises"
        )

        assert " ".join(response.metadata.authors) == "H. John B. Birks"
        assert response.metadata.journal_name == None

    def test_different_dois(self, event_loop, list_doi_title, oa_repo):
        i, (doi, title) = list(enumerate(list_doi_title))[0]
        responses = [
            event_loop.run_until_complete(
                self.wrap_with_session(queries.DoiQuery(i, doi), oa_repo)
            )
            for i, (doi, title) in enumerate(list_doi_title)
        ]

        for response, (doi, title) in zip(responses, list_doi_title):
            assert (
                    repositories.strings_approx_equal(
                        response.metadata.title, title
                    )
                    == True
            )

    def test_failing_doi_query(self, event_loop, failing_query, oa_repo):
        with pytest.raises(DataNotFoundError):
            event_loop.run_until_complete(
                self.wrap_with_session(
                    queries.DoiQuery(1, failing_query[0]), oa_repo
                )
            )

    def test_incorrect_title_query(
            self, event_loop, title_that_does_not_exist_query, oa_repo
    ):
        with pytest.raises(DataNotFoundError):
            event_loop.run_until_complete(
                self.wrap_with_session(
                    title_that_does_not_exist_query, oa_repo
                )
            )
