from datetime import date

import pytest

from sources.data_processing.paper_scraper_api import PaperScraper
from sources.data_processing.queries import ISSNTimeIntervalQuery, \
    KeywordQuery


class TestPaperScraper:
    @pytest.fixture
    def sample_journal_query(self):
        return ISSNTimeIntervalQuery(0,
                                    "1420 - 9101",
                                     date(2018, 1, 1),
                                     date(2019, 1, 1),
                                    )

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
    def failing_kw_query(self):
        return KeywordQuery(2, title="Algae growth by shading")

    def test_accepts_queries(self, kw_query, failing_kw_query,
                             sample_journal_query):
        with PaperScraper() as ps:
            ps.delegate_query(kw_query)
            ps.delegate_query(failing_kw_query)
            #ps.delegate_query(sample_journal_query)
            delegated = {0, 1, 2}
            while True:
                result = ps.poll_response(True)
                print(result)
                delegated = delegated - result.query_id
                if len(delegated) == 0:
                    break
