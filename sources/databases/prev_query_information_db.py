import json
from pathlib import Path
from typing import Set, List

from sources.databases.daterange_util import Daterange, DaterangeUtility


class PrevQueryInformation:
    """The Database that stores the previously queried timeframes for each journal. 
        This will help us reduce the number of "double" queries. Usage must always be
        done in combination with the context pattern.
    """    
    document_path = Path(__file__).parent / "file_databases" / \
                    "prev_journal_query_information.json" #Moved to __init__

    def __init__(self):
        self._database_object = None
        document_path = Path(__file__).parent / "file_databases" / \
                    "prev_journal_query_information.json"
                    
    def insert_successful_query(self, issn: str, date_range: Daterange):
        """Inserts a successful query for journal with ISSN issn and for the Daterange date_range.

        Args:
            issn (str): The issn of the journal for which we want to note down a successful query.
            date_range (Daterange): The daterange for which we performed a successful query.
        """        
        if issn in self._database_object.keys() \
                and self._database_object[issn] is not None:
            self._database_object[issn].add(date_range)
        else:
            self._database_object[issn] = {date_range}

    def get_journal_dateranges(self, issn: str) -> Set[Daterange]:
        """Get the set of all already queried Dateranges for journal with ISSN issn.

        Args:
            issn (str): The ISSN of the journal we want to look up.

        Returns:
            Set[Daterange]: The set of Dateranges we already queried.
        """        
        return self._database_object[issn] if issn in self._database_object.keys() \
            else set()

    def merge_ranges(self, issn: str):
        """Merge ranges updates the set of queried ranges for journal with ISSN issn by combining the ranges stored for it.

        Args:
            issn (str): The ISSN of the journal for which we want to perform the reduction.
        """        
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
