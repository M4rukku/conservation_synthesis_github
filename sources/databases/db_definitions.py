import json
import textwrap
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class DBArticleMetadata:
    """Class for structuring data stored in the article database

    It contains all possible information we can obtain from a query."""

    title: str
    authors: list
    doi: str
    publication_date: str  # date ISO Format yyyy-mm-dd or just yyyy
    abstract: str
    repo_identifier: str  # Which repo gave us the data
    language: str = "EN"
    publisher: Optional[str] = None
    journal_name: Optional[str] = None
    journal_volume: Optional[str] = None
    journal_issue: Optional[str] = None
    issn: Optional[str] = None
    url: Optional[str] = None

    sync_date: Optional[str] = None
    checked: bool = False

    classified: Optional[str] = None
    relevant: bool = False
    relevance_score: Optional[float] = None

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