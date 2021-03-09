from sources.databases.db_definitions import DBArticleMetadata
from sources.databases.internal_databases import InternalSQLDatabase
from sources.frontend.user_queries import ResultFilter


@dataclass
class DBArticleMetadata:
    """Class for structuring stored data in the database

    It contains all possible information we can obtain from a query."""

    title: str
    authors: list
    doi: str
    publication_date: str  # date ISO Format yyyy-mm-dd or just yyyy
    abstract: str
    repo_identifier: str  # Which repo gave us the data
    language: str = "EN"
    publisher: str = None
    journal_name: str = None
    journal_volume: str = None
    journal_issue: str = None
    issn: str = None
    url: str = None

    sync_date: str = None
    checked: bool = None

    classified: str = None
    relevant: bool = None

    def to_json(self):
        return json.dumps(asdict(self))

    def as_dict(self):
        return asdict(self)

    def __repr__(self):
        returnString = f"""\n \n Title: {self.title} 
            \n Authors: {", ".join(self.authors)} 
            \n Published: {self.publication_date} \n DOI: {self.doi}"""

        if self.abstract is not None:
            returnString += f"""\n Abstract: \n {textwrap.fill(self.abstract,
                                                               width=80)} \n\n"""
        return returnString


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

    # mock data for testing table display
    def perform_mock_filter_query(self, filter_: ResultFilter):
        result = []
        article = DBArticleMetadata(title='Title',
                                    authors=['Author One, Author Two'],
                                    doi='https://doi.org/10.1000/182',
                                    publication_date='2021',
                                    abstract='Abstract',
                                    repo_identifier='ID')
        result.append(article)
        result.append(article)
        result.append(article)
        result.append(article)
        result.append(article)
        result.append(article)
        result.append(article)
        result.append(article)
        return result


    def store_article(self, metadata: DBArticleMetadata):
        """Takes the metadata object and stores it in the internal database.

        Args:
            metadata (DBArticleMetadata): The metadata to store in the database.
        """
        self._internal_db.store_article(metadata)

    #Setup Connection
    def __enter__(self):
        self._internal_db.initialise()
        return self

    # Teardown Connection
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._internal_db.terminate()
