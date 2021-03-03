from datetime import date

import pytest

from sources.databases.daterange_util import Daterange
from sources.databases.journal_name_issn_database import JournalNameIssnDatabase
from sources.databases.prev_query_information_db import PrevQueryInformation


class TestPrevQueryInformationDatabase:

    def test_store_data_works(self):
        drA = Daterange(
            date(2018, 1, 1),
            date(2019, 1, 1))

        drB = Daterange(
            date(2001, 1, 1),
            date(2002, 1, 1))

        with PrevQueryInformation() as pqi:
            pqi.insert_successful_query("555666666-555", drA)
            pqi.insert_successful_query("555666666-555", drB)

        with PrevQueryInformation() as pqi:
            assert pqi.get_journal_dateranges("555666666-555") == {drA, drB}


class TestJournalNameISSNDatabase:
    @pytest.fixture
    def entries(self):
        return [("0006-3207", "biological conservation"),
                ("0006-3657", "bird study")]

    def test_name_query(self, entries):
        with JournalNameIssnDatabase() as db:
            for issn, name in entries:
                assert db.get_name_from_issn(issn) == name

    def test_issn_query(self, entries):
        with JournalNameIssnDatabase() as db:
            for issn, name in entries:
                assert db.get_issn_from_name(name) == issn
