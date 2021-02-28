from sources.data_processing.paper_scraper_api import PaperScraper
from sources.ml_model.ml_model import MlModelWrapper
from sources.databases.article_data_db import MariaRepositoryAPI, \
    DBArticleMetadata
from sources.databases.prev_query_information_db import DocumentDatabase, \
    Daterange
from sources.frontend.user_queries import UserQueryResponse, \
    UserQueryInformation


class QueryDispatcher:
    def __init__(self):
        self._classifier = MlModelWrapper()
        self._article_db = MariaRepositoryAPI()
        self._paper_scraper = PaperScraper()
        self._prev_query_data = DocumentDatabase()

    def process_query(self, query: UserQueryInformation) -> UserQueryResponse:
        """ Processes a user query instantly! Returns what is known so far,
        and tells the user that the rest will be loaded in the future

        :param query: A UserQueryInformation object
        """
        pass

    def _separate_query_into_known_and_unknown_date_parts(self, query:
    UserQueryInformation):
        pass

    def _load_and_synchronize_in_background(self, query:
    UserQueryInformation, uknown_date_ranges: list[Daterange]):
        pass
