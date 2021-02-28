import csv
from recordclass import recordclass

"""
Each row can be indexed in array-style, e.g. cleancsv[3432]
The fields within each row can then be accessed in one of 3 ways:

cleancsv[3432][3]
cleancsv[3432]["authors"]
cleancsv[3432].authors

Rows and fields can also be iterated on.
The 'authors' and 'topics' fields are arrays of strings.
"""
class CleanCSV:
    # specify the path of the csv to read
    def __init__(self, path):
        infile = open(path, newline="", encoding='utf-8')
        reader = csv.reader(infile)
        # take the field names from the first line
        self.fields = next(reader)
        Row = recordclass("Row", self.fields)
        self.data = list(map(Row._make, reader))
        # split the authors field into individual authors
        # (requires field in file to be formatted correctly)
        for jRow in range(len(self.data)):
            self._format_field(jRow)

    def _format_field(self, rowIndex):
        row = self.data[rowIndex]
        if "authors" in self.fields:
            if row.authors != "":
                row.authors = row.authors.split("; ")
            else:
                row.authors = []
        if "topics" in self.fields:
            row.topics = row.topics.split("; ")

    # write the current state to a file
    def write_file(self, path):
        with open(path, "w") as outfile:
            writer = csv.writer(outfile, dialect="unix")
            # write the column headers first!
            writer.writerow(self.fields)
            # go row by row in order to concatenate the authors list.
            for row in self.data:
                newrow = row
                if "authors" in self.fields:
                    newrow.authors = "; ".join(row.authors)
                if "topics" in self.fields:
                    newrow.topics = "; ".join(row.topics)
                writer.writerow(newrow)

    # remove a row from the csv
    def pop(self, index):
        self.data.pop(index)
    
    # sort the rows by the value of a given field
    def sort(self, field):
        if field == "index":
            self.data = sorted(self.data, key=lambda row: int(row["index"]))
        else:
            self.data = sorted(self.data, key=lambda row: row[field])
    
    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n < len(self.data):
            item = self.data[self.n]
            self.n += 1
            return item
        else:
            raise StopIteration
    
    def __len__(self):
        return len(self.data)
