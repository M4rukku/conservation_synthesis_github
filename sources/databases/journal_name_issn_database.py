import json
from pathlib import Path


class ISSNNotFoundError(Exception):
    pass


class JournalNameNotFoundError(Exception):
    pass


class JournalNameIssnDatabase:
    document_path = Path(
        __file__).parent / "file_databases" / "issn_journal_map.json"

    def __init__(self):
        self._issn_name_db = None
        self._name_issn_db = None

    def get_issn_from_name(self, name: str):
        name = name.lower().strip()
        if name in self._name_issn_db.keys():
            return self._name_issn_db[name]
        else:
            raise ISSNNotFoundError(f"Journal Name: {name} is not in database")

    def get_name_from_issn(self, issn: str) -> list:
        if issn in self._issn_name_db.keys():
            return self._issn_name_db[issn]
        else:
            raise ISSNNotFoundError(f"ISSN: {issn} is not in database")

    def __enter__(self):
        with self.document_path.open("r") as f:
            self._issn_name_db = json.load(f)
            self._issn_name_db = {key: val.lower().strip() for key, val in
                                  self._issn_name_db.items()}
            self._name_issn_db = {val: key for key, val in
                                  self._issn_name_db.items()}
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
