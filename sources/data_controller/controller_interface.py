from sources.data_controller.controller import QueryDispatcher
from sources.frontend.user_queries import UserQueryInformation, \
    UserQueryResponse


class UserQueryHandler:
    def __init__(self):
        self._dispatcher = QueryDispatcher()

    def process_user_query(self,
                           query: UserQueryInformation) -> UserQueryResponse:
        return self._dispatcher.process_query(query)
