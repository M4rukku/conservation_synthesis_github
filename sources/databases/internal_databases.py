import abc
import sqlite3
from pathlib import Path

from sources.databases.db_definitions import DBArticleMetadata
from sources.frontend.user_queries import ResultFilter


def authors_to_string(authors: list):
    return ";".join(authors) if isinstance(authors, list) else authors


def author_string_to_list(author_string):
    return author_string.split(";")


class InternalSQLDatabase(metaclass=abc.ABCMeta):

    def __init__(self):
        pass

    @abc.abstractmethod
    def set_checked(self, doi):
        pass

    @abc.abstractmethod
    def perform_filter_query(self, filter_: ResultFilter):
        pass

    @abc.abstractmethod
    def store_article(self, metadata: DBArticleMetadata):
        pass

    @abc.abstractmethod
    def initialise(self):
        pass

    @abc.abstractmethod
    def terminate(self):
        pass


class SQLiteDB(InternalSQLDatabase):
    database_path = Path(__file__).parent / "file_databases" / \
                    "article_data.sqlite"

    def __init__(self):
        super().__init__()
        self.con = None

    def set_checked(self, doi):
        pass

    def perform_filter_query(self,
                             filter_: ResultFilter):
        cur = self.con.cursor()

        #BASE QUERY
        entries = [filter_.from_pub_date.isoformat(),
                   filter_.to_pub_date.isoformat()]

        query = """SELECT * FROM articles 
        WHERE date(?) >= publication_date
        AND date(?) <= publication_date """

        # ADD SYNC DATE
        if filter_.from_sync_date is not None:
            query += "AND date(?) <= sync_date"

        questionmarks = "?" * len(filter_.journal_names)
        query += 'AND journal_name IN ({})'.format(', '.join(questionmarks))

    def store_article(self, metadata: DBArticleMetadata):
        cur = self.con.cursor()

        insertion = """INSERT INTO articles(title, authors, doi, 
        publication_date, abstract, repo_identifier, "language", publisher,
        journal_name, journal_volume, journal_issue, issn, url, sync_date, 
        checked, classified, relevant) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
        ?,?) """

        data = (metadata.title,
                authors_to_string(metadata.authors),
                metadata.doi,
                metadata.publication_date,
                metadata.abstract,
                metadata.repo_identifier,
                metadata.language,
                metadata.publisher,
                metadata.journal_name,
                metadata.journal_volume,
                metadata.journal_issue,
                metadata.issn,
                metadata.url,
                metadata.sync_date,
                1 if metadata.checked else 0,
                metadata.classified,
                1 if metadata.relevant else 0)
        try:
            cur.execute(insertion, data)
        except Exception as e:
            pass

    def initialise(self):
        self.con = sqlite3.connect(self.database_path)

    def terminate(self):
        self.con.commit()
        self.con.close()