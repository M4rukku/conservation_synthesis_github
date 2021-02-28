import pytest
from sources.data_processing.queries import KeywordQuery


class TestKeywordQuery:
    @pytest.fixture
    def sample_query(self):
        return KeywordQuery(
            1,
            authors=["H. John", "B. Birk"],
            title=r"Ecological palaeoecology and conservation biology: controversies, challenges, and compromises",
            journal_name=None,
            doi="10.1080/21513732.2012.701667",
            start_date=None,
            end_date=None,
        )

    def test_dict_is_correct(self, sample_query):
        assert sample_query.authors == ["H. John", "B. Birk"]
        assert sample_query.doi == "10.1080/21513732.2012.701667"
        assert sample_query.start_date is None
        assert (
            sample_query.title
            == r"Ecological palaeoecology and conservation biology: controversies, challenges, and compromises"
        )
