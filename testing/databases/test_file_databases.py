from datetime import date
from sources.databases.prev_query_information_db import PrevQueryInformation, \
    Daterange
from datetime import date

from sources.databases.prev_query_information_db import PrevQueryInformation, \
    Daterange


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

