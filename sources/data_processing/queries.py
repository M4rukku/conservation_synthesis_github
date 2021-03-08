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
    url: str = None

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


@dataclass
class JournalData:
    """A piece of data that can be added to a response. It is used because different repositories know different things about the data. 
    ... In order to obtain everything we will use this on the Response. (Mostly on DOIQueries, where I know the journal via the sync method in controller.)
    """
    journal_name: str
    journal_volume: str
    journal_issue: str
    publication_date: str
    issn: str


class Response:
    """Class encapsulating a Response.

    It contains all information we obtained from a article based query."""

    def __init__(self, query_id: int, metadata: ArticleMetadata):
        self.query_id = query_id
        self.metadata = metadata

    @staticmethod
    def valid(field: str):
        return field is not None and field != ""

    def add_journal_data(self, journal_data):
        if journal_data is not None:
            if self.valid(journal_data.publication_date):
                self.metadata.publication_date = journal_data.publication_date
            if self.valid(journal_data.journal_name):
                self.metadata.journal_name = journal_data.journal_name
            if self.valid(journal_data.journal_volume):
                self.metadata.journal_volume = journal_data.journal_volume
            if self.valid(journal_data.journal_issue):
                self.metadata.journal_issue = journal_data.journal_issue
            if self.valid(journal_data.issn):
                self.metadata.issn = journal_data.issn


class FailedQueryResponse(Response):
    """Class indicating a query failure."""
    def __init__(self, query_id):
        super().__init__(query_id, None)


class JournalDaterangeResponse(Response):
    """Class encapsulating a response from a ISSNDaterangeQuery."""
    
    def __init__(self, query_id: int, all_articles: list):
        super().__init__(query_id, None)
        self.query_id = query_id
        self.all_articles = all_articles


# Interface Definition
################################################################################

class AbstractQuery(metaclass=abc.ABCMeta):
    """The interface each query must implement. Queries can be passed to repositories to obtain a response object.

    ... At the very least each query contains an ID and SchedulingInformations (all already queried repositories saved by their identifier.)
    ... I have added Journal Data as a persistent data storage over query redelegation in the QueryDelegator.
    """    
    def __init__(self, query_id: int):
        self._query_id = query_id
        self._queried_repositories = set()
        self._journal_data = None

    @property
    def query_id(self):
        return self._query_id

    def store_scheduling_information(self, repo_identifier):
        self._queried_repositories.add(repo_identifier)

    def get_scheduling_information(self):
        return self._queried_repositories

    def add_journal_data(self, journal_data):
        self._journal_data = journal_data

    def get_journal_data(self):
        return self._journal_data


# Scheduling Information contains data about tried APIs and more?
# It must at least contain key "tried_connections"

# Concrete Query Definitions
################################################################################


class DoiQuery(AbstractQuery):
    """A Doi query is a query awaiting a response based only on the doi of the article we want.
    """    
    def __init__(self, query_id: int, doi_to_query: str, ):
        super().__init__(query_id)
        self.doi_to_query = doi_to_query


class ISSNTimeIntervalQuery(AbstractQuery):
    """A ISSNTimeIntervalQuery query is a query awaiting a response based on the ISSN of a journal and a date range.
    """  
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
    """A KeywordQuery queries the repositories based on bibliographic data and timeranges.
    """    
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
