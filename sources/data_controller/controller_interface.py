from frontend.user_queries import UserQueryInformation, UserQueryResponse
from sources.data_controller.controller import QueryDispatcher
from frontend.user_queries import UserQueryInformation, \
    UserQueryResponse


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
                           ) -> UserQueryResponse:
        return self._dispatcher.process_query(query,
                                              fetch_article_cb,
                                              fetch_article_cb_freq,
                                              classify_data_cb,
                                              classify_data_cb_freq,
                                              finished_execution_cb
                                              )
