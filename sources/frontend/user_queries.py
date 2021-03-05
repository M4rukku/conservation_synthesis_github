import datetime
from dataclasses import dataclass

classification_types = ["Amphibians",
                        "Animals",
                        "ex - situ",
                        "Bacteria"
                        "Behaviour change",
                        "Birds",
                        "Coastal",
                        "Farmland",
                        "Fish",
                        "Forests / Woodland",
                        "Fungi",
                        "Grassland / Savanna",
                        "Individual plant / algae population",
                        "Invasive or problem amphibians",
                        "Invasive or problem bacteria / other living agents",
                        "Invasive or problem birds",
                        "Invasive or problem fish",
                        "Invasive or problem fungi",
                        "Invasive or problem invertebrates",
                        "Invasive or problem mammals",
                        "Invasive or problem plants / algae",
                        "Invasive or problem reptiles",
                        "Invertebrates",
                        "Mammals",
                        "Marine",
                        "Marine invertebrates",
                        "Plants / algae Ex Situ",
                        "Reptiles",
                        "Rivers, lakes and lagoons, Sustainable aquaculture",
                        "Wetlands"]


# query object created on search page
@dataclass
class UserQueryInformation:
    journals_to_query: list
    start_date_range: datetime.date
    end_date_range: datetime.date
    relevant_only: bool = None
    classification_restriction: str = None


class UserQueryResponse:
    def __init__(self, processed_data: list, message=None):
        self.processed_data = processed_data  # Data from Database
        self.message = message  # What still needs to be gathered (intervals)i


# query object created on results page
class ResultFilter:
    def __init__(self,
                 journal_names: list,
                 relevant_only: bool = None,
                 remove_checked_articles: bool = None,
                 classification: str = None,

                 from_pub_date: datetime.date = None,
                 to_pub_date: datetime.date = None,
                 from_sync_date: datetime.date = None,
                 to_sync_date: datetime.date = None,
                 ):
        self.journal_names = journal_names
        self.relevant_only = relevant_only
        self.remove_checked_articles = remove_checked_articles
        self.classification = classification

        self.from_pub_date = from_pub_date
        self.to_pub_date = to_pub_date
        self.from_sync_date = from_sync_date
        self.to_sync_date = to_sync_date
