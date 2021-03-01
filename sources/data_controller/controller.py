from sources.data_processing.paper_scraper_api import PaperScraper
from sources.databases.article_data_db import MariaRepositoryAPI
from sources.databases.journal_name_issn_database import JournalNameIssnDatabase
from sources.databases.prev_query_information_db import PrevQueryInformation, \
    Daterange
from sources.frontend.user_queries import UserQueryResponse, \
    UserQueryInformation
from sources.ml_model.ml_model import MlModelWrapper


class InvalidTimeRangeError(Exception):
    pass


class QueryDispatcher:
    def __init__(self):
        self._classifier = MlModelWrapper(None)
        self._article_db = MariaRepositoryAPI()
        self._paper_scraper = PaperScraper()

    def process_query(self, query: UserQueryInformation) -> UserQueryResponse:
        """ Processes a user query instantly! Returns what is known so far,
        and tells the user that the rest will be loaded in the future

        :param query: A UserQueryInformation object
        """
        #Check Validity of Daterange
        if query.end_date_range <= query.start_date_range:
            raise InvalidTimeRangeError

        query_range = Daterange(query.start_date_range, query.end_date_range)

        #Get Data We already have:
        with JournalNameIssnDatabase() as db:
            issns = {name: db.get_issn_from_name(name)
                     for name in query.journals_to_query}

        with PrevQueryInformation() as db:
            ranges = {name: db.get_journal_dateranges(issns[name])
                      for name in query.journals_to_query}
        
        #What do we still need to query -- Split query_range
        
    def _separate_query_into_known_and_unknown_date_parts(self, query:
    UserQueryInformation, issns: dict):

    def _load_and_synchronize_in_background(self, query:
    UserQueryInformation, unknown_date_ranges: list[Daterange]):
        pass
