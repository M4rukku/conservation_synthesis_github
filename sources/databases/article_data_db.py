import datetime
import json
import textwrap
from dataclasses import dataclass, asdict
from typing import List

from frontend.user_queries import ResultFilter


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
    def __init__(self):
        pass

    def general_query(self, journal_name: str, start_date: str, end_date:
    str, relevant: bool = None, classification=None) -> List[DBArticleMetadata]:
        pass

    def perform_filter_query(self,
                             filter_: ResultFilter):
        pass

    def store_article(self, metadata: DBArticleMetadata):
        pass

    #Setup COnnection
    def __enter__(self):
        pass

    #Teardown Connection
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass