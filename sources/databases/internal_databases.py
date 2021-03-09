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
    def set_checked(self, doi: str, checked: bool):
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

    def set_checked(self, doi:str, checked:bool):
        pass

    def perform_filter_query(self,
                             filter_: ResultFilter):
        cur = self.con.cursor()

        # BASE QUERY
        entries = [filter_.from_pub_date.isoformat(),
                   filter_.to_pub_date.isoformat()]

        query = "SELECT * FROM articles WHERE publication_date >= date(?) AND publication_date <= date(?)"

        # SYNC DATES
        if filter_.from_sync_date is not None:
            entries.append(filter_.from_sync_date.isoformat())
            query += " AND sync_date >= date(?)"

        if filter_.to_sync_date is not None:
            entries.append(filter_.to_sync_date.isoformat())
            query += " AND sync_date <= date(?)"

        # JOURNAL LIST
        entries.extend(filter_.journal_names)
        journal_placeholders = "?" * len(filter_.journal_names)
        query += " AND journal_name IN ({})".format(', '.join(journal_placeholders))

        # BOOLS
        if filter_.relevant_only:
            query += " AND relevant = 1"

        if filter_.remove_checked_articles:
            query += " AND checked = 0"

        # CLASSIFICATION
        if filter_.classification is not None:
            entries.append(filter_.classification)
            query += " AND classified = ?"

        try:
            cur.execute(query, entries)
            return cur.fetchall()
        except Exception as e:
            return None

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
