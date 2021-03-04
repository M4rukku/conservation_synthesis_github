from frontend.user_queries import UserQueryInformation, UserQueryResponse
from sources.data_controller.controller import QueryDispatcher

class UserQueryHandler:
    def __init__(self):
        self._dispatcher = QueryDispatcher()

    def process_user_query(self, query: UserQueryInformation) -> UserQueryResponse:
        pass