import aiohttp
import asyncio
import json
from cleancsv import CleanCSV

csv = CleanCSV("cleaned_references.csv")

api_key = "Bb6GprzvsKnLSFxlimUhP1XaJfwo4Ruc"

# Article Search

search_url = "https://core.ac.uk:443/api-v2/articles/search"

async def request(row):
    query_elements = []
    if row.title != "":
        query_elements.append(f'title:"{row.title}"')
    if row.authors != []:
        query_elements.append(f'authors:({" ".join(row.authors)})')
    if row.doi != "":
        query_elements.append(f'doi:"{row.doi}"')
    if row.pub_year != "":
        query_elements.append(f'year:"{row.pub_year}"')
    query_string = " AND ".join(query_elements)
    queries = [
        {
            "query": query_string,
            "page": 1,
            "pageSize": 10,
            "scrollId": ""
        }
    ]
    #print(query_string)
    search_body = json.dumps(queries)
    search_params = {
            "apiKey": api_key,
    }
    timeout = aiohttp.ClientTimeout(total=10000)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(search_url, data=search_body, params=search_params) as r:
            response = json.loads(await r.text())
            try:
                print(response[0]["data"][0])
                abstract = response[0]["data"][0]["description"]
                #print(abstract)
            except:
                print("="*70)

async def main():
    await asyncio.gather(*(request(csv[i]) for i in range(8292, 18292)))

asyncio.run(main())
print(found, scanned)
