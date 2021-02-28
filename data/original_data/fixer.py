from cleancsv import CleanCSV
import jellyfish

exclude = [
    "<rozas2001.pdf>",
    "Waterfowl collection; in Severn Wildfowl Trust Fifth Annual Report (Wildfowl Vol5)"
]

def approx(fst_string: str, snd_string: str) -> bool:
    if fst_string in exclude:
        return False
    dist = jellyfish.damerau_levenshtein_distance(
    fst_string.strip().lower(), snd_string.strip().lower()
    )
    return (
    True
    if dist < (1 + (len(fst_string) + len(snd_string)) // 40)
    else False
    )

csv = CleanCSV("cleaned_references.csv")
csv.sort("title")

total = 0
i = 0
while i < len(csv)-1:
    while approx(csv[i].title, csv[i+1].title):
        total += 1
        print(csv[i].title)
        print(csv[i+1].title)
        for topic in csv[i+1].topics:
            if topic not in csv[i].topics:
                csv[i].topics.append(topic)
        csv.pop(i+1)
    i += 1

csv.sort("index")
csv.write_file("outfile.csv")
print(total)
