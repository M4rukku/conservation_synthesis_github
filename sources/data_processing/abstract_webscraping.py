import re
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import unquote
import pandas as pd
import time
import random
from concurrent.futures import as_completed, ThreadPoolExecutor
   
    
urlreg = re.compile(
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)


def get_abstract_from_doi(doi: str):
    """Takes a DOI as string and returns an abstract scraped from www.doi.org/doi.

    Args:
        doi (str): The DOI to query

    Returns:
        str: The queried abstract or None, if nothing was found.
    """
    scraper = cloudscraper.create_scraper()
    doi_data = scraper.get(f"https://www.doi.org/{doi}", timeout=10)
    doi_bs = BeautifulSoup(doi_data.text)

    if doi_data.url.startswith(
        "https://link.springer.com/"
    ) and not doi_data.url.startswith("https://link.springer.com/article"):
        cleaned_link = doi_data.url.replace(
            "https://link.springer.com/", "https://link.springer.com/article/"
        )
        doi_data = scraper.get(cleaned_link, timeout=10)
        doi_bs = BeautifulSoup(doi_data.text)

    # Check whether we landed at a javascript redirect page
    attempts = 0
    while len(doi_bs.get_text()) < 150:
        if attempts > 3:
            return None
        attempts = attempts + 1
        pattern = re.compile(r"\?Redirect=(.*);")
        match = pattern.search(doi_bs.head.__str__())
        if match is not None:
            doi_data = scraper.get(unquote(match.group(1)), timeout=10)
            doi_bs = BeautifulSoup(doi_data.text)
        else:
            res = doi_bs.body.find_all(
                id=re.compile("url|redirect", flags=re.IGNORECASE)
            )
            for tag in res:
                red_url = filter(
                    lambda v: v is not None,
                    [
                        urlreg.search(unquote(val))
                        for key, val in tag.attrs.items()
                    ],
                )
                red_url = list(red_url)
                if len(red_url) > 0:
                    match = red_url[0]
                    doi_data = scraper.get(unquote(match.group(1)), timeout=10)
                    doi_bs = BeautifulSoup(doi_data.text)
                    continue

    doi_bs = doi_bs.body

    res3 = doi_bs.find_all(
        re.compile(r"h[1-5]|text|pharos-heading"),
        string=re.compile(r"Summary|Abstract", flags=re.IGNORECASE),
    )
    if len(res3) > 0:
        res3 = res3[0]
        sibling = res3.next_element
        while sibling.name not in ["section", "p", "div"]:
            sibling = sibling.next_element
        return sibling.get_text().strip()

    # Method 1
    res1 = doi_bs.find_all(re.compile("section|p|div"), class_="abstract")
    if len(res1) > 0:
        res1 = res1[0]
        return res1.get_text().strip()

    # Search readable text -- fallback
    readable_text = doi_bs.get_text()
    pattern = re.compile(
        r"\n\s*Abstract\s*(.*)\n|\n\s*Summary\s*(.*)\n", flags=re.IGNORECASE
    )
    result = pattern.search(readable_text)

    return result.group(1).strip() if result is not None else None


def update_dict_w_abstract(row):
    """If passed a dictionary containing a DOI, it will try to scrape an abstract from the web and store it under the key "abstract". 

    Args:
        row (dict): A dictionary containing at least a doi field. 

    Returns:
        dict: A dict with an updated abstract field.
    """
    try:
        row["abstract"] = get_abstract_from_doi(row["doi"]).strip()
    except Exception as e:
        row["abstract"] = None
    return row


def query_abstract_from_dois_with_delay(
    data: pd.DataFrame, delay, start=0, end=0
):
    """Queries abstract using the doi fields in the Dataframe data. Returns a new Dataframe with scraped abstracts. After every query, it will pause for delay seconds to prevent being blocked.

    Args:
        data (pd.DataFrame): A Dataframe having at least a column containing DOIs.
        delay (float): The time to wait after each query.
        start (int, optional): After which row (position) to start querying. Defaults to 0.
        end (int, optional): At which row (position) to end querying. Defaults to 0.

    Returns:
        (pd.DataFrame): Returns a new Dataframe containing an additional row "abstracts".
    """
    start = start
    end = len(data) if end == 0 else end
    acc = []
    for ind, (_, row) in enumerate(data.iterrows()):
        if ind < start:
            continue
        if ind > end:
            break
        time.sleep(random.uniform(delay - 0.25, delay + 0.25))
        acc.append(update_dict_w_abstract(row))
    return pd.DataFrame(acc)


def query_abstract_from_dois_using_multithreading(
    data: pd.DataFrame, start=0, end=0
):
    """Queries abstract using the doi fields in the Dataframe data. Returns a new Dataframe with scraped abstracts. It uses multithreading for fast results; this may lead to IP blocks, so take care when using it.

    Args:
        data (pd.DataFrame): A Dataframe having at least a column containing DOIs.
        start (int, optional): After which row (position) to start querying. Defaults to 0.
        end (int, optional): At which row (position) to end querying. Defaults to 0.

    Returns:
        (pd.DataFrame): Returns a new Dataframe containing an additional row "abstracts".
    """
    start = start
    end = len(data) if end == 0 else end
    scrape = []
    accF = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        for ind, (_, row) in enumerate(data.iterrows()):
            if ind < start:
                continue
            if ind > end:
                break
            accF.append(executor.submit(update_dict_w_abstract, row))

        for future in as_completed(accF):
            try:
                datas = future.result()
                scrape.append(datas)
            except Exception as exc:
                print("generated an exception: %s" % (exc))

    return pd.DataFrame(scrape)
