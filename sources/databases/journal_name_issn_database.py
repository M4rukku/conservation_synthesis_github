import json
from pathlib import Path


class ISSNNotFoundError(Exception):
    pass


class JournalNameIssnDatabase:
    """The Database that associates journal names with their respective ISSN. 
        It will first perform a .lower.strip transformation on the journal_name to standardise the mapping.
    
    Must be used with the context pattern.
    """    
    document_path = Path(
        __file__).parent / "file_databases" / "issn_journal_map.json"

    def __init__(self):
        self._issn_name_db = None
        self._name_issn_db = None

    def get_issn_from_name(self, name: str):
        """Returns ISSN when given a journal_name as string.

        Args:
            name (str): The journal name to query (case is unimportant).
        Raises:
            ISSNNotFoundError: Returns if the ISSN is not in the Database.

        Returns:
            str: The ISSN associated with name.
        """        
        name = name.lower().strip()
        if name in self._name_issn_db.keys():
            return self._name_issn_db[name]
        else:
            raise ISSNNotFoundError(f"Journal Name: {name} is not in database")

    def get_name_from_issn(self, issn: str) -> str:
        """Returns the journal name if given an ISSN.

        Args:
            issn (str): The ISSN we want to lookup.

        Raises:
            ISSNNotFoundError: Raised when the ISSN does not map to any name in the db.

        Returns:
            str: The name associated with the ISSN.
        """        
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
