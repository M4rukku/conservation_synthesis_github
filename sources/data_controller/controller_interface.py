import datetime

from sources.data_controller.controller import QueryDispatcher
from sources.databases.article_data_db import ArticleRepositoryAPI
from sources.frontend.user_queries import UserQueryInformation


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


class ResultFilter:
    def __init__(self,
                 journal_names: list,
                 relevant_only: bool = None,
                 remove_checked_articles: bool = None,
                 classification: str = None,

                 from_pub_date: datetime.date = None,
                 to_pub_date: datetime.date = None,
                 from_sync_date: datetime.date = None,
                 to_sync_date: datetime.date = None,
                 ):
        self.journal_names = journal_names
        self.relevant_only = relevant_only
        self.remove_checked_articles = remove_checked_articles
        self.classification = classification

        self.from_pub_date = from_pub_date
        self.to_pub_date = to_pub_date
        self.from_sync_date = from_sync_date
        self.to_sync_date = to_sync_date


class DatabaseResultQueryHandler:

    def process_filter_query(self, filter_: ResultFilter):
        result = None
        with ArticleRepositoryAPI() as db:
            result = db.perform_filter_query(filter_)
        return result
