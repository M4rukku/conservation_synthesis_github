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
