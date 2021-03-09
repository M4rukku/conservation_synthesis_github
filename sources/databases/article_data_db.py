from sources.databases.db_definitions import DBArticleMetadata
from sources.databases.internal_databases import InternalSQLDatabase
from sources.frontend.user_queries import ResultFilter


class ArticleRepositoryAPI:
    """ArticleRepositoryAPI defines the interface for interaction with an InternalSQLDatabase. 
    
    It provides all possible commands for interaction with the database in the project context and shall always be used to access the article database.
    
    Examples:
        Always use the ArticleRepositoryAPI in combination with the context pattern.
        
        >>> with ArticleRepositoryAPI(SQLiteDB()) as db:
        ...     db.store_article(metadata)
    
    """

    def __init__(self, internal_db: InternalSQLDatabase):
        self._internal_db = internal_db

    def set_checked(self, doi: str, checked: bool):
        """Searches for a DOI in the database and updates the entry's checked field to checked.

        Args:
            doi (str): The entry to modify, indexed by DOI.
            checked (bool): The value to set checked to.
        """        
        self._internal_db.set_checked(doi, checked)

    def perform_filter_query(self,
                             rfilter: ResultFilter):
        """Returns all articles in the database that fulfill the filter criteria specified in rfilter.

        Args:
            rfilter (ResultFilter): The ResultFilter by which we want to specify the response.

        Returns:
            List[DBArticleMetadata]: All responses fulfilling the properties specified in rfilter.
        """
        return self._internal_db.perform_filter_query(rfilter)

    def store_article(self, metadata: DBArticleMetadata):
        """Takes the metadata object and stores it in the internal database.

        Args:
            metadata (DBArticleMetadata): The metadata to store in the database.
        """
        self._internal_db.store_article(metadata)

    # Setup COnnection
    def __enter__(self):
        self._internal_db.initialise()
        return self

    # Teardown Connection
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._internal_db.terminate()
