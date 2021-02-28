from pathlib import Path
import json


class Daterange:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date


class DocumentDatabase:
    document_path = Path(".") / "prev_journal_data" / "doc_database"

    def __init__(self):
        self._database_object = None

    def insert_successful_query(self, journal_name: str, start_date: str,
                                end_date: str):
        pass

    def get_journal_dateranges(self, journal_name: str) -> list[Daterange]:
        pass

    def __enter__(self):
        try:
            with self.document_path.open("r") as f:
                self._database_object = json.loads(f)
        except Exception:
            self._database_object = {}

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self.document_path.open("w") as f:
            json.dump(self._database_object, f)
