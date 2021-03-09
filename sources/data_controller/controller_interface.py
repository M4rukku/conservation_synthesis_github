from sources.databases.db_definitions import DBArticleMetadata
from sources.data_controller.controller import QueryDispatcher
from sources.databases.article_data_db import ArticleRepositoryAPI
from sources.databases.internal_databases import SQLiteDB
from sources.frontend.user_queries import ResultFilter
from sources.frontend.user_queries import UserQueryInformation
from typing import Callable, List

# handles search user queries
class UserQueryHandler:
    """Interface between Controller and Frontend.
       Handles synchronisation queries of the user by delegating to the QueryDispatcher.
    """
    def __init__(self):
        self._dispatcher = QueryDispatcher()

    def process_user_query(self,
                           query: UserQueryInformation,
                           fetch_article_cb: Callable[[int, float], None]=None,
                           fetch_article_cb_freq=100,
                           classify_data_cb: Callable[[int, float], None]=None,
                           classify_data_cb_freq=100,
                           finished_execution_cb: Callable[[], None]=None
                           ):
        """Delegates a synchronisation query to be done in the background. Has the option to add callbacks which will be called periodically.

        Args:
            query (UserQueryInformation): The Synchronisation query to perform.
            fetch_article_cb (Callable[[int, float], None], optional): The callback that will be called after fetch_article_cb_freq articles have been queried. Defaults to None.
            fetch_article_cb_freq (int, optional): The frequency of calling fetch_article_cb. Defaults to 100.
            classify_data_cb (Callable[[int, float], None], optional): The callback that will be called after classify_data_cb_freq articles have been classified. Defaults to None.
            classify_data_cb_freq (int, optional): The frequency of calling classify_data_cb_freq. Defaults to 100.
            finished_execution_cb (Callable[[], None], optional): The callback to be called once the query has successfully finished. Defaults to None.
        """
        self._dispatcher.process_query(query,
                                       fetch_article_cb,
                                       fetch_article_cb_freq,
                                       classify_data_cb,
                                       classify_data_cb_freq,
                                       finished_execution_cb
                                       )


# handles results filter queries
class DatabaseResultQueryHandler:
    """DatabaseResultQueryHandler is the interface to obtain data from the database.
    """

    @staticmethod
    def process_filter_query(rfilter: ResultFilter) -> List[DBArticleMetadata]:
        """Performs a filter query on the database using the restrictions imposed by ResultFilter.

        Args:
            rfilter (ResultFilter): The filter we have to apply to the data.

        Returns:
            List[DBArticleMetadata]: The articles fitting the search criteria
        """
        result = None
        with ArticleRepositoryAPI(SQLiteDB()) as db:
            result = db.perform_filter_query(rfilter)
        return result

    # currently calling a mock function instead of real data
    def process_mock_filter_query(self, filter_: ResultFilter):
        db = ArticleRepositoryAPI()
        result = db.perform_mock_filter_query(filter_)
        return result