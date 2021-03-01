import math
import threading

from sources.data_processing.queries import ISSNTimeIntervalQuery
from sources.databases.article_data_db import MariaRepositoryAPI
from sources.databases.journal_name_issn_database import JournalNameIssnDatabase
from sources.databases.prev_query_information_db import PrevQueryInformation, \
    Daterange, DaterangeUtility
from sources.frontend.user_queries import UserQueryResponse, \
    UserQueryInformation


class InvalidTimeRangeError(Exception):
    pass


def get_unknown_date_ranges(query: UserQueryInformation):
    journal_names = query.journals_to_query

    # Get Data We already have:
    with JournalNameIssnDatabase() as db:
        issns = {name: db.get_issn_from_name(name)
                 for name in journal_names}

    with PrevQueryInformation() as db:
        ranges = {name: db.get_journal_dateranges(issns[name])
                  for name in journal_names}

    # What do we still need to query -- Split query_range
    # Remove ranges from query_range -- NOTE: PER JOURNAL!
    query_ranges = \
        {name: {Daterange(query.start_date_range,
                          query.end_date_range)} for name in journal_names}

    for name, range in query_ranges:
        known_ranges = ranges[name]
        for kr in known_ranges:
            range_cpy = set()
            for subrange in range:
                if DaterangeUtility.intersects(kr, subrange):
                    range_cpy.add(
                        DaterangeUtility.
                            remove_interval_from_range(kr, subrange))
                else:
                    range_cpy.add(subrange)
            range = range_cpy
        query_ranges[name] = range

    return query_ranges


class QueryDispatcher:
    def __init__(self):
        pass

    def process_query(self, query: UserQueryInformation) -> UserQueryResponse:
        """ Processes a user query instantly! Returns what is known so far,
        and tells the user that the rest will be loaded in the future

        :param query: A UserQueryInformation object
        """
        # Check Validity of Daterange
        if query.end_date_range <= query.start_date_range:
            raise InvalidTimeRangeError

        unknown_date_ranges = get_unknown_date_ranges(query)

        # Dispatch the unknown ranges to be queried in the bg
        thread = threading.Thread(
            target=self._load_and_synchronize_in_background,
            args=(query, unknown_date_ranges))

        thread.daemon = True
        thread.start()

        response = []
        with MariaRepositoryAPI() as db:
            for name in query.journals_to_query:
                response.append(
                    db.general_query(name,
                                     query.start_date_range,
                                     query.end_date_range,
                                     query.relevant_only,
                                     query.classification_restriction))
        missing_information = \
            [name + " Missing Ranges: \n" + "   ".join(map(str, ls_date_range))
             for name, ls_date_range in unknown_date_ranges]

        missing_information = "\n\n".join(missing_information)

        return \
            UserQueryResponse(response,
                              f"Missing Information: {missing_information}")

    def _load_and_synchronize_in_background(self, query:
    UserQueryInformation, unknown_date_ranges):
        # Change to Paper Scraper Queries

        with JournalNameIssnDatabase() as db:
            issns = {name: db.get_issn_from_name(name)
                     for name in query.journals_to_query}

        queries = []
        query_id = 0

        for name, ranges in unknown_date_ranges:
            issn = issns[name]
            for rnge in ranges:
                delta = rnge.end_date - rnge.start_date
                days = delta.days
                #SPLIT
                count = 0
                split = int(math.ceil(days / 90.0))
                step = days / split
                while count < days:
                    queries.append(
                        ISSNTimeIntervalQuery(query_id, issn, rnge.start_date,
                                              rnge.start_date + step))
                    query_id = query_id + 1

        all_queries =