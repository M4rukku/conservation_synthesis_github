import abc
import datetime
import json
import textwrap
from dataclasses import dataclass, asdict


@dataclass
class ArticleMetadata:
    """Class for structuring response metadata information.

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
    url: str = None  # TODO REMOVE

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


class Response:
    """Class encapsulating a Response.

    It contains all possible information we can obtain from a query."""

    def __init__(self, query_id: int, metadata: ArticleMetadata):
        self.query_id = query_id
        self.metadata = metadata


class FailedQueryResponse(Response):
    def __init__(self, query_id):
        super().__init__(query_id, None)


class JournalDaterangeResponse(Response):
    def __init__(self, query_id: int, all_articles: list):
        super().__init__(query_id, None)
        self.query_id = query_id
        self.all_articles = all_articles


# Interface Definition
################################################################################

class AbstractQuery(metaclass=abc.ABCMeta):
    def __init__(self, query_id: int):
        self._query_id = query_id
        self._queried_repositories = set()

    @property
    def query_id(self):
        return self._query_id

    def store_scheduling_information(self, repo_identifier):
        self._queried_repositories.add(repo_identifier)

    def get_scheduling_information(self):
        return self._queried_repositories


# Scheduling Information contains data about tried APIs and more?
# It must at least contain key "tried_connections"

# Concrete Query Definitions
################################################################################


class DoiQuery(AbstractQuery):
    def __init__(self, query_id: int, doi_to_query):
        super().__init__(query_id)
        self.doi_to_query = doi_to_query


class ISSNTimeIntervalQuery(AbstractQuery):
    def __init__(
            self,
            query_id: int,
            issn: str,
            start_interval_date: datetime.date,
            end_interval_date: datetime.date,
    ):
        super().__init__(query_id)
        self.start_interval_date = start_interval_date
        self.end_interval_date = end_interval_date
        self.issn = issn


class KeywordQuery(AbstractQuery):
    def __init__(
            self,
            query_id: int,
            authors: list = None,
            title: str = None,
            journal_name: str = None,
            doi: str = None,
            start_date: datetime.date = None,
            end_date: datetime.date = None,
    ):
        super().__init__(query_id)
        self.query_keywords = {
            "authors": authors if authors is not None else None,
            "title": title if title is not None else None,
            "journal": journal_name if journal_name is not None else None,
            "doi": doi if doi is not None else None,
            "start_date": start_date if start_date is not None else None,
            "end_date": end_date if end_date is not None else None,
        }

    @property
    def authors(self):
        return self.query_keywords["authors"]

    @property
    def title(self):
        return self.query_keywords["title"]

    @property
    def journal(self):
        return self.query_keywords["journal"]

    @property
    def start_date(self):
        return self.query_keywords["start_date"]

    @property
    def end_date(self):
        return self.query_keywords["end_date"]

    @property
    def doi(self):
        return self.query_keywords["doi"]
