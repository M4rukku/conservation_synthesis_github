import pytest

from ..frontend.user_queries import UserQueryInformation


@pytest.fixture()
def sample_user_query():
    return UserQueryInformation(0)


def test_convert_user_to_paper_scraper_query():
    assert False
