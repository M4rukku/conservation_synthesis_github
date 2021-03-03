import json
from datetime import date
from pathlib import Path


class Daterange:
    def __init__(self, start_date: date, end_date: date):
        self._start_date = start_date
        self._end_date = end_date

    @staticmethod
    def from_string(start_date: str, end_date: str):
        return Daterange(date.fromisoformat(start_date),
                         date.fromisoformat(end_date))

    def __lt__(self, other):
        return self.start_date < other.start_date

    @property
    def start_date(self):
        return self._start_date

    @property
    def end_date(self):
        return self._end_date

    def __eq__(self, other):
        if not isinstance(other, Daterange):
            return False
        else:
            return self.start_date == other.start_date and self.end_date == \
                   other.end_date

    def __hash__(self):
        return hash((self.start_date, self.end_date))

    def __str__(self):
        return f"Daterange: From - {self.start_date.isoformat()}, " \
               f"To - {self.end_date.isoformat()} \n"


class DaterangeUtility:
    @staticmethod
    def intersects(date1: Daterange, date2: Daterange):
        return (date1.start_date <= date2.start_date <= date1.end_date) or \
               (date2.start_date <= date1.start_date <= date2.end_date)

    @staticmethod
    def remove_interval_from_range(to_remove: Daterange, range: Daterange) -> \
            list:
        """If there is an intersection, this function will remove to_remove
        from range.
        """

        # 4 Cases -- R... Remove, D... Daterange
        # R..D..R..D; D..R..R..D; D..R..D..R; R..D..D..R
        if to_remove.start_date <= range.start_date:
            # R..D..R..D or R..D..D..R
            if to_remove.end_date < range.end_date:
                return [Daterange(to_remove.end_date, range.end_date)]
            else:
                return []
        else:  # D..R..R..D; D..R..D..R
            if to_remove.end_date < range.end_date:
                # D..R..R..D
                return [Daterange(range.start_date, to_remove.start_date),
                        Daterange(to_remove.end_date, range.end_date)]
            else:
                return [Daterange(range.start_date, to_remove.start_date)]

    @staticmethod
    def reduce_ranges(ranges: set) -> set:
        ranges = list(ranges)
        ranges.sort()
        new_ranges = set()

        cur_range = ranges[0]
        i = 1
        while i < len(ranges):
            if cur_range.end_date >= ranges[i].start_date:
                cur_range = Daterange(cur_range.start_date,
                                      max(cur_range.end_date,
                                          ranges[i].end_date))
            else:
                new_ranges.add(cur_range)
                cur_range = ranges[i]
            i = i + 1

        new_ranges.add(cur_range)
        return new_ranges


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
