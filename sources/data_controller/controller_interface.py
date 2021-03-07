from sources.data_controller.controller import QueryDispatcher
from sources.databases.article_data_db import ArticleRepositoryAPI
from sources.databases.internal_databases import SQLiteDB
from sources.frontend.user_queries import ResultFilter
from sources.frontend.user_queries import UserQueryInformation


# handles search user queries
class UserQueryHandler:
    def __init__(self):
        self._dispatcher = QueryDispatcher()

    def process_user_query(self,
                           query: UserQueryInformation,
                           fetch_article_cb=None,
                           fetch_article_cb_freq=100,
                           classify_data_cb=None,
                           classify_data_cb_freq=100,
                           finished_execution_cb=None
                           ):
        self._dispatcher.process_query(query,
                                       fetch_article_cb,
                                       fetch_article_cb_freq,
                                       classify_data_cb,
                                       classify_data_cb_freq,
                                       finished_execution_cb
                                       )


# handles results filter queries
class DatabaseResultQueryHandler:

    def process_filter_query(self, filter_: ResultFilter):
        result = None
        with ArticleRepositoryAPI(SQLiteDB()) as db:
            result = db.perform_filter_query(filter_)
        return result
