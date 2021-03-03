import itertools
from datetime import date

import pytest

from .controller import QueryDispatcher
from ..data_processing.queries import ISSNTimeIntervalQuery
from ..databases.daterange_util import Daterange


# @pytest.fixture()
# def sample_user_query():
#     return UserQueryInformation(date(2016, 1, 1), date(2021, 9, 7),)

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
    #WORKS DOING MANUAL TESTING
