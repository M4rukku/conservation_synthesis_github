from sources.databases.db_definitions import DBArticleMetadata
from sources.databases.internal_databases import InternalSQLDatabase
from sources.frontend.user_queries import ResultFilter


class ArticleRepositoryAPI:
    def __init__(self, internal_db: InternalSQLDatabase):
        self._internal_db = internal_db

    def set_checked(self, doi):
        self._internal_db.set_checked(doi)

    def perform_filter_query(self,
                             filter_: ResultFilter):
        return self._internal_db.perform_filter_query(filter_)

    def store_article(self, metadata: DBArticleMetadata):
        self._internal_db.store_article(metadata)

    #Setup COnnection
    def __enter__(self):
        self._internal_db.initialise()

    #Teardown Connection
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._internal_db.terminate()