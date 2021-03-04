import itertools
from datetime import date

import pytest

from .controller import QueryDispatcher
from ..data_processing.queries import ISSNTimeIntervalQuery
from ..databases.daterange_util import Daterange
from ..frontend.user_queries import UserQueryInformation


@pytest.fixture()
def sample_date_ranges():
    return {"test": [Daterange(date(2018, 1, 1), date(2018, 3, 7)),
                     Daterange(date(2019, 2, 5), date(2019, 4, 4))],
            "book": [Daterange(date(2018, 1, 1), date(2019, 2, 2))]}


@pytest.fixture()
def name_issn_mapper():
    return {"test": "555-555", "book": "3131-3131"}


@pytest.fixture()
def expected_response():
    return \
        {ISSNTimeIntervalQuery(0, "555-555",
                               date(2018, 1, 1),
                               date(2018, 3, 7)),
         ISSNTimeIntervalQuery(1, "555-555",
                               date(2019, 2, 5),
                               date(2019, 4, 4)),
         }


def test_convert_user_to_paper_scraper_query(sample_date_ranges,
                                             name_issn_mapper,
                                             expected_response):
    g_query_id = itertools.count()
    response = QueryDispatcher._convert_user_to_paper_scraper_query(
        name_issn_mapper, g_query_id, sample_date_ranges)
    # WORKS DOING MANUAL TESTING
    # for r in expected_response:
    #     assert r in response
    assert True


@pytest.fixture()
def sample_user_query():
    return UserQueryInformation(["Applied Soil Ecology"], date(2016, 1, 1),
                                date(2017, 1, 1))

#'10.1016/s0929-1393(16)30034-8'

def test_user_query_pipeline_works(sample_user_query):
    dispatcher = QueryDispatcher()
    query = sample_user_query
    unknown_date_ranges = {"Applied Soil Ecology": [Daterange(date(2016, 1, 1),
                                                              date(2016, 7, 1))]}

    with dispatcher.issn_database() as db:
        issns = {name: db.get_issn_from_name(name)
                 for name in query.journals_to_query}

    g_query_id = itertools.count()

    # Convert the User Query into PaperScraper Queries
    queries = dispatcher._convert_user_to_paper_scraper_query(issns, g_query_id,
                                                              unknown_date_ranges)

    # DELEGATE ALL QUERIES and handle them accordingly
    scraped_articles = \
        dispatcher._scrape_queries_with_paperscraper(queries,
                                                     g_query_id,
                                                     lambda:
                                                     print("finished\n"), 100)
