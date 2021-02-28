import abc
import datetime
import functools
import json
import re
from collections import defaultdict

import habanero
import yaml
import jellyfish

import requests
from habanero import Crossref

import asyncio
import aiohttp

from . import queries
from .queries import AbstractQuery
from aiohttp import ClientSession


# Interface Definitions
###############################################################################
class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


class AbstractRepository(metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def get_identifier():
        pass

    @property
    @abc.abstractmethod
    def api_endpoint(self):
        raise NotImplementedError("Must declare api endpoint!")

    @property
    @abc.abstractmethod
    def max_queries_per_second(self):
        raise NotImplementedError(
            "Must declare how many queries per second are allowed!"
        )

    @abc.abstractmethod
    async def execute_query(
            self, query: AbstractQuery, session: ClientSession = None
    ) -> queries.Response:
        raise NotImplementedError("Must declare how queries are handled!")

# Concrete Repositories
######################################################################################################

# Utilities
############################################


class DataNotFoundError(Exception):
    pass


def strings_approx_equal(fst_string: str, snd_string: str) -> bool:
    dist = jellyfish.damerau_levenshtein_distance(
        fst_string.strip().lower(), snd_string.strip().lower()
    )
    return (
        True
        if dist < (2 + (len(fst_string) + len(snd_string)) // 40)
        else False
    )


def get_metadata_best_fit_by_title(ls_metadata, real_title):
    lev_distances = [
        jellyfish.damerau_levenshtein_distance(
            meta.title.strip().lower(), real_title.strip().lower()
        )
        for meta in ls_metadata
    ]
    candidate_responses = list(
        filter(
            lambda pair: pair[1] < (2 + len(ls_metadata[pair[0]].title) // 20),
            enumerate(lev_distances),
        )
    )

    if len(candidate_responses) > 0:
        response = min(candidate_responses, key=lambda pair: pair[1])
        return ls_metadata[response[0]]
    else:
        return None


# Makes Author search more secure by deleting all abbreviated names
author_pattern = re.compile(r"\s(.\.)\s|^(.\.)\s|(.\.)$")
symbol_pattern = re.compile(r'''[,;"':]''')
whitespace_pattern = re.compile(r"\s+")


def format_author(author: str):
    author = symbol_pattern.sub("", author)
    cur_pos = 0
    reduced_str = ""
    count = 0
    while count < 5:
        count += 1
        match = author_pattern.search(author[cur_pos:])
        if match is not None:
            reduced_str += author[cur_pos: (cur_pos + match.start())] + " "
            cur_pos = cur_pos + match.end()
        else:
            reduced_str += author[cur_pos:]
            break

    return whitespace_pattern.sub(" ", reduced_str).strip()


class OpenAireRepository(AbstractRepository):
    @staticmethod
    def get_identifier():
        return "openaire"

    @property
    def api_endpoint(self):
        return "http://api.openaire.eu/search/publications"

    @property
    def max_queries_per_second(self):
        return 15  # Potentially more concurrent connections

    async def _request_json_api(
            self, session: ClientSession, params: dict
    ) -> str:
        """GET request wrapper to fetch page HTML.

        kwargs are passed to `session.request()`.
        """
        resp = await session.request(
            method="GET", url=self.api_endpoint, params=params
        )
        resp.raise_for_status()
        text = await resp.text()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return yaml.load(text, yaml.SafeLoader)

    @staticmethod
    def _get_oa_query_dict_from_args(
            authors: list = None,
            from_date_accepted: datetime.date = None,
            to_date_accepted: datetime.date = None,
            title: str = None,
            doi: str = None,
            size: int = 5,
    ):
        query_keywords = {}
        query_keywords["format"] = "json"
        query_keywords["size"] = str(size)

        if authors is not None:
            query_keywords["author"] = " ".join(
                [format_author(author) for author in authors]
            )
        if from_date_accepted is not None:
            query_keywords["fromDateAccepted"] = from_date_accepted.isoformat()
        if to_date_accepted is not None:
            query_keywords["toDateAccepted"] = to_date_accepted.isoformat()
        if title is not None:
            query_keywords["title"] = title
        if doi is not None:
            query_keywords["doi"] = doi
        return query_keywords

    def _get_oa_query_dict_from_keyword_query(self, query):
        return self._get_oa_query_dict_from_args(
            query.authors,
            query.start_date,
            query.end_date,
            query.title,
            query.doi,
        )

    def _map_oa_entity_to_metadata(self, oa_entity) -> queries.ArticleMetadata:
        meta_dict = {
            "authors": [
                author_data["$"] for author_data in oa_entity["creator"]
            ]
            if isinstance(oa_entity["creator"], list)
            else [oa_entity["creator"]["$"]],
            "repo_identifier": self.get_identifier(),
            "publisher": oa_entity["publisher"]["$"]
            if "publisher" in oa_entity
            else None,
            "abstract": oa_entity["description"]["$"]
            if "description" in oa_entity
            else None,
        }

        if isinstance(oa_entity["pid"], list):
            doi_id = list(
                filter(
                    lambda entry: entry["@classid"] == "doi", oa_entity["pid"]
                )
            )
            meta_dict["doi"] = doi_id[0]["$"] if len(doi_id) > 0 else None
        else:
            meta_dict["doi"] = (
                oa_entity["pid"]["$"]
                if oa_entity["pid"]["@classid"] == "doi"
                else None
            )

        title = list(
            filter(
                lambda entry: entry["@classid"] == "main title",
                oa_entity["title"],
            )
        )
        title = title[0]["$"] if len(title) > 0 else oa_entity["title"][0]["$"]
        meta_dict["title"] = title.strip()

        if "relevantdate" in oa_entity:
            if isinstance(oa_entity["relevantdate"], list):
                publicised = list(
                    filter(
                        lambda entry: entry["@classid"] == "published-print",
                        oa_entity["relevantdate"],
                    )
                )
                publicised = (
                    publicised[0]["$"] if len(publicised) > 0 else None
                )
            else:
                publicised = (
                    oa_entity["relevantdate"]["$"]
                    if oa_entity["relevantdate"]["@classid"]
                       == "published-print"
                    else None
                )
            meta_dict["publication_date"] = publicised

        if "journal" in oa_entity:
            journal_data = oa_entity["journal"]
            vol = journal_data["vol"] if "vol" in journal_data else None
            iss = journal_data["iss"] if "iss" in journal_data else None
            issn = journal_data["issn"] if "issn" in journal_data else None
            name = journal_data["$"] if "$" in journal_data else None
            meta_dict["journal_volume"] = vol
            meta_dict["journal_issue"] = iss
            meta_dict["journal_name"] = name
            meta_dict["issn"] = issn

        return queries.ArticleMetadata(**meta_dict)

    def _get_best_fit_metadata_from_response(self, query, json_response):

        if json_response["response"]["results"] is None:
            raise DataNotFoundError

        oaf_result_list = json_response["response"]["results"]["result"]
        oaf_result_entities = [
            result["metadata"]["oaf:entity"]["oaf:result"]
            for result in oaf_result_list
        ]

        # Return best match if we have multiple answers
        entities_metadata = [
            self._map_oa_entity_to_metadata(entity)
            for entity in oaf_result_entities
        ]

        # Assume title is known (doi queries return empty results)
        if hasattr(query, "title") and query.title is not None:
            to_return = get_metadata_best_fit_by_title(
                entities_metadata, query.title
            )
            if to_return is None:
                raise DataNotFoundError()
            else:
                return to_return

        else:  # TODO Improve on this!
            return entities_metadata[0]

    async def execute_query(
            self, query: AbstractQuery, session: ClientSession = None
    ):
        if isinstance(query, queries.KeywordQuery):
            metadata = self._get_best_fit_metadata_from_response(
                query,
                await self._request_json_api(
                    session, self._get_oa_query_dict_from_keyword_query(query)
                ),
            )

            return queries.Response(query_id=query.query_id, metadata=metadata)
        if isinstance(query, queries.DoiQuery):
            kw_query = queries.KeywordQuery(
                query_id=query.query_id, doi=query.doi_to_query
            )
            return await self.execute_query(kw_query, session)
        else:
            raise NotImplementedError(
                f"{self.get_identifier()} does not support the query type {type(query)}"
            )


class CrossrefRepository(AbstractRepository):
    _polite_pool_mail = ""

    @staticmethod
    def get_identifier():
        return "crossref"

    @property
    def api_endpoint(self):
        raise NotImplementedError("Access via Habanero!")

    _calculated = None

    @property
    def max_queries_per_second(self):
        if CrossrefRepository._calculated is None:
            cr = requests.head("https://api.crossref.org/")
            CrossrefRepository._calculated = int(
                cr.headers["x-rate-limit-limit"]) / int(
                cr.headers["x-rate-limit-interval"][:-1]
            )
        return CrossrefRepository._calculated

    def _execute_query_new_thread(self, query: AbstractQuery):
        if isinstance(query, queries.KeywordQuery):
            metadata = self._get_best_fit_metadata_from_response(
                query, self._execute_keyword_query(query)
            )
            return queries.Response(query_id=query.query_id, metadata=metadata)

        elif isinstance(query, queries.DoiQuery):
            return self._execute_query_new_thread(
                queries.KeywordQuery(
                    query_id=query.query_id, doi=query.doi_to_query
                )
            )
        elif isinstance(query, queries.JournalTimeIntervalQuery):
            return self._execute_journal_time_interval_query(query)

        else:
            raise NotImplementedError()

    async def execute_query(
            self, query: AbstractQuery, session: ClientSession = None
    ):
        return await asyncio.get_running_loop().run_in_executor(
            None, functools.partial(self._execute_query_new_thread, query)
        )

    naive_clean_abstract = re.compile(r"<jats:\w*>|</jats:\w*>")

    def _map_response_item_to_metadata(self, item):
        return queries.ArticleMetadata(
            **{
                "title": item.get("title")[0],
                "authors": None
                if "author" not in item
                else [
                    author_f.get("given", "") + author_f.get("family")
                    for author_f in item["author"]
                ],
                "abstract": self.naive_clean_abstract.sub(
                    "", item.get("abstract")
                )
                if "abstract" in item
                else None,
                "doi": item.get("DOI", None),
                "publisher": item.get("publisher", None),
                "journal_volume": item.get("volume", None),
                "journal_issue": item.get("issue", None),
                "issn": item.get("ISSN")[0] if "ISSN" in item else None,
                "url": item.get("URL", None),
                "publication_date": "-".join(
                    map(str, item.get("issued")["date-parts"][0])
                ),
                "repo_identifier": self.get_identifier(),
            }
        )

    def _get_best_fit_metadata_from_response(self, query, response):
        if response["message"] is None:
            raise DataNotFoundError()

        candidate_items = (
            response["message"]["items"]
            if "items" in response["message"]
            else [response["message"]]
        )
        candidate_metadata = [
            self._map_response_item_to_metadata(item)
            for item in candidate_items
        ]

        if hasattr(query, "title") and query.title is not None:
            best_metadata = get_metadata_best_fit_by_title(
                candidate_metadata, query.title
            )
            if best_metadata is not None:
                return best_metadata
            else:
                raise DataNotFoundError()
        else:  # TODO Improve
            return candidate_metadata[0]

    def _execute_keyword_query(self, query):
        cr = Crossref(mailto=self._polite_pool_mail)

        if query.doi is not None:
            try:
                response = cr.works(ids=query.doi)
            except requests.exceptions.HTTPError as e:
                raise DataNotFoundError(
                    "DOI is invalid or not reachable from Crossref!"
                ) from e
        else:
            to_select = [
                "abstract",
                "title",
                "original-title",
                "issue",
                "short-title",
                "DOI",
                "issued",
                "volume",
                "author",
                "URL",
                "ISSN",
                "publisher",
            ]
            kwargs = {}
            if query.title is not None:
                kwargs["query_bibliographic"] = query.title
            if query.authors is not None:
                kwargs["query_author"] = " ".join(
                    [format_author(author) for author in query.authors]
                )

            filter = {"type": "journal-article"}
            if query.start_date is not None:
                filter["from-pub-date"] = query.start_date.isoformat()
            if query.end_date is not None:
                filter["until-pub-date"] = query.start_date.isoformat()

            response = cr.works(
                limit=5, **kwargs, select=to_select, filter=filter
            )

        if type(response) is list:
            if len(response) == 0:
                raise DataNotFoundError
            else:
                return response[0]
        else:
            return response

    def _execute_journal_time_interval_query(self, query):
        pass


class CoreRepository(AbstractRepository):
    api_key = "Bb6GprzvsKnLSFxlimUhP1XaJfwo4Ruc"

    @staticmethod
    def get_identifier():
        return "CORE"

    @property
    def api_endpoint(self):
        return "https://core.ac.uk:443/api-v2/articles/search"

    @property
    def max_queries_per_second(self):
        return 15  # !!! Couldn't actually find this info on the CORE website

    async def execute_query(
            self, query: AbstractQuery, session: ClientSession = None
    ) -> queries.Response:
        if isinstance(query, queries.KeywordQuery):
            (search_body, search_params) = self._kw_query_to_params(query)
            r = await session.post(
                self.api_endpoint, data=search_body, params=search_params
            )
            response = json.loads(await r.text())
            metadata = self._response_to_metadata(response)
            return queries.Response(query_id=query.query_id, metadata=metadata)
        else:
            raise NotImplementedError(
                f"{self.get_identifier()} does not support the query type {type(query)}"
            )

    # converts an AbstractQuery into parameters for a search request.
    def _kw_query_to_params(self, query):
        query_elements = []
        if query.title is not None:
            query_elements.append(f'title:"{query.title}"')
        if query.authors is not None:
            query_elements.append(f'authors:({" ".join(query.authors)})')
        if query.doi is not None:
            query_elements.append(f'doi:"{query.doi}"')
        year_start = (
            query.start_date.year if query.start_date is not None else "*"
        )
        year_end = query.end_date.year if query.end_date is not None else "*"
        if year_start is not None or year_end is not None:
            query_elements.append(f"year:[{year_start} TO {year_end}]")
        query_string = " AND ".join(query_elements)
        queries = [
            {"query": query_string, "page": 1, "pageSize": 10, "scrollId": ""}
        ]
        search_body = json.dumps(queries)
        search_params = {
            "apiKey": self.api_key,
        }
        return (search_body, search_params)

    def _response_to_metadata(self, response: dict):
        try:
            top_result = response[0]["data"][0]
        except:
            raise DataNotFoundError()
        metadata_dict = {
            "title": "",
            "authors": [],
            "doi": "",
            "publication_date": "",
            "abstract": "",
            "repo_identifier": self.get_identifier(),
            "language": "",
            "publisher": "",
            "journal_name": "",
            "journal_volume": "",
            "journal_issue": "",
            "issn": "",
            "url": "",
        }

        default_top_result = defaultdict(lambda: None, top_result)
        metadata_dict["title"] = default_top_result["title"]
        metadata_dict["authors"] = default_top_result["authors"]
        metadata_dict["doi"] = default_top_result["doi"]
        metadata_dict["publication_date"] = default_top_result["year"]
        metadata_dict["abstract"] = default_top_result["description"]
        metadata_dict["publisher"] = default_top_result["publisher"]

        return queries.ArticleMetadata(**metadata_dict)
