import json
from pathlib import Path

from sources.databases.daterange_util import Daterange, DaterangeUtility


class PrevQueryInformation:
    document_path = Path(__file__).parent / "file_databases" / \
                    "prev_journal_query_information.json"

    def __init__(self):
        self._database_object = None

    def insert_successful_query(self, issn: str, date_range: Daterange):
        if issn in self._database_object.keys() \
                and self._database_object[issn] is not None:
            self._database_object[issn].add(date_range)
        else:
            self._database_object[issn] = {date_range}

    def get_journal_dateranges(self, issn: str) -> list:
        return self._database_object[
            issn] if issn in self._database_object.keys() \
            else {}

    def merge_ranges(self, issn: str):
        ranges = self._database_object[issn]
        self._database_object[issn] = DaterangeUtility.reduce_ranges(ranges)

    def __enter__(self):
        try:
            with self.document_path.open("r") as f:
                self._database_object = json.load(f)
                self._database_object = {
                    issn: set([Daterange.from_string(start, end)
                               for start, end in dates])
                    for issn, dates in self._database_object.items()}
        except Exception as e:
            self._database_object = {}
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._database_object is not None \
                and len(self._database_object.items()) > 0:
            with self.document_path.open("w") as f:
                # Remove Sets
                # Remove DateRange
                to_dump = {key: [[date.start_date.isoformat(),
                                  date.end_date.isoformat()] for date in
                                 dates] for key, dates in
                           self._database_object.items()}
                json.dump(to_dump, f)
