import datetime
import itertools
import math
import random
import threading
from datetime import timedelta
from typing import Iterator, List, Dict, Generator, Set, Callable, Optional

from sources.data_processing.paper_scraper_api import PaperScraper
from sources.data_processing.queries import ISSNTimeIntervalQuery, Response, \
    JournalDaterangeResponse, FailedQueryResponse, DoiQuery, KeywordQuery, \
    ArticleMetadata, JournalData
from sources.databases.article_data_db import ArticleRepositoryAPI
from sources.databases.daterange_util import Daterange, DaterangeUtility
from sources.databases.db_definitions import DBArticleMetadata
from sources.databases.internal_databases import SQLiteDB, InternalSQLDatabase
from sources.databases.journal_name_issn_database import JournalNameIssnDatabase
from sources.databases.prev_query_information_db import PrevQueryInformation
from sources.frontend.user_queries import UserQueryInformation
from sources.ml_model.ml_model import MlModelWrapper


class InvalidTimeRangeError(Exception):
    pass


def get_unknown_date_ranges(query: UserQueryInformation) -> Dict[str, Set[Daterange]]:
    """Decomposes the synchronisation query into multiple subqueries, by removing dateranges we have looked at before.

    Args:
        query (UserQueryInformation): The query to decompose

    Returns:
        Dict[str, Set[Daterange]]: The dateranges we need to query for each journal name.
    """
    journal_names = query.journals_to_query

    # Get Data We already have:
    with JournalNameIssnDatabase() as db:
        issns = {name: db.get_issn_from_name(name)
                 for name in journal_names}

    with PrevQueryInformation() as db:
        ranges = {name: db.get_journal_dateranges(issns[name])
                  for name in journal_names}

    # What do we still need to query -- Split query_range
    # Remove ranges from query_range -- NOTE: PER JOURNAL!
    query_ranges = \
        {name: {Daterange(query.start_date_range,
                          query.end_date_range)} for name in journal_names}

    for name, range in query_ranges.items():
        known_ranges = ranges[name]
        query_ranges[name] = \
            DaterangeUtility.remove_known_ranges(known_ranges, range)

    # By default we always want to "requery" the top 1 Month of articles, if the query asks for a
    # current timerange
    if datetime.date.today() >= query.end_date_range >= (datetime.date.today() - timedelta(days=15)):
        last_month = (datetime.date.today() - timedelta(days=30))
        start_interval = max(last_month, query.start_date_range)
        for name, range in query_ranges.items():
            query_ranges[name].add(Daterange(start_interval, datetime.date.today()))
            query_ranges[name] = DaterangeUtility.reduce_ranges(query_ranges[name])

    return query_ranges

def map_to_db_metadata(article: ArticleMetadata, relevant: bool):
    return DBArticleMetadata(title=article.title,
                             authors=article.authors,
                             doi=article.doi,
                             publication_date=article.publication_date,
                             abstract=article.abstract,
                             repo_identifier=article.repo_identifier,
                             language=article.language,
                             publisher=article.publisher,
                             journal_name=article.journal_name,
                             journal_volume=article.journal_volume,
                             journal_issue=article.journal_issue,
                             issn=article.issn,
                             url=f"https://doi.org/{article.doi}",
                             relevant=relevant,
                             classified="NA",
                             checked=False,
                             sync_date=datetime.date.today().isoformat())


class QueryDispatcher:
    """The QueryDispatcher processes synchronisation queries in the background by offering the process_query interface.
    """

    def __init__(self,
                 issn_database: Optional[JournalNameIssnDatabase] = None,
                 article_database: Optional[InternalSQLDatabase] = None):

        self.issn_database = \
            JournalNameIssnDatabase() if issn_database is None else issn_database
        if issn_database is None:
            self.article_database: InternalSQLDatabase = SQLiteDB()
        else:
            self.article_database: InternalSQLDatabase = article_database

    def process_query(self, query: UserQueryInformation,
                      start_execution_cb,
                      fetch_article_cb, fetch_article_cb_freq,
                      classify_data_cb, classify_data_cb_freq,
                      finished_execution_cb) -> None:

        """Starts a thread that runs the synchronisation query in the background. 

        Args:
            query (UserQueryInformation): The Synchronisation query to perform.
            start_execution_cb (Callable[[], None]): The callback to be called at the start of program execution.
            fetch_article_cb (Callable[[int, float], None], optional): The callback that will be called after fetch_article_cb_freq articles have been queried. Defaults to None.
            fetch_article_cb_freq (int, optional): The frequency of calling fetch_article_cb. Defaults to 100.
            classify_data_cb (Callable[[int, float], None], optional): The callback that will be called after classify_data_cb_freq articles have been classified. Defaults to None.
            classify_data_cb_freq (int, optional): The frequency of calling classify_data_cb_freq. Defaults to 100.
            finished_execution_cb (Callable[[], None], optional): The callback to be called once the query has successfully finished. Defaults to None.

        Raises:
            InvalidTimeRangeError: Raised when timerange is invalid iff end_date < start_date
        """

        # Check Validity of Daterange
        if query.end_date_range <= query.start_date_range:
            raise InvalidTimeRangeError

        # Dispatch the unknown ranges to be queried in the bg
        thread = threading.Thread(
            target=self._load_and_synchronize_in_background,
            args=(query, start_execution_cb,
                  fetch_article_cb, fetch_article_cb_freq,
                  classify_data_cb, classify_data_cb_freq,
                  finished_execution_cb))

        thread.daemon = True
        thread.start()
        # Removed from implementation, might be interesting ing the future
        # response = []
        # with self.article_database() as db:
        #     for name in query.journals_to_query:
        #         response.append(
        #             db.general_query(name,
        #                              query.start_date_range,
        #                              query.end_date_range,
        #                              query.relevant_only,
        #                              query.classification_restriction))
        # missing_information = \
        #     [name + " Missing Ranges: \n" + "   ".join(map(str, ls_date_range))
        #      for name, ls_date_range in unknown_date_ranges]
        #
        # missing_information = "\n\n".join(missing_information)
        #
        # return \
        #     UserQueryResponse(response,
        #                       f"Missing Information: {missing_information}")

    def _load_and_synchronize_in_background(self, query: UserQueryInformation,
                                            start_execution_cb,
                                            fetch_article_cb,
                                            fetch_article_cb_freq,
                                            classify_data_cb,
                                            classify_data_cb_freq,
                                            finished_execution_cb):
        """Performs the synchronisation query in six steps:
                1) get_unknown_date_ranges (What do I really need to query?, Remove already queried information.)
                2) _convert_user_to_paper_scraper_query - Decompose the DateRanges we still need to query into PaperScraper Queries.
                3) _scrape_queries_with_paperscraper  - Scrape the Queries.
                4) Classify the returned articles with the ML Model wrapper
                5) Store the metadata into the ArticleMetadataDB
                6) Store the information about the performed queries into prev_query_information.

        Args:
            query (UserQueryInformation): The Synchronisation query to perform.
            fetch_article_cb (Callable[[int, float], None], optional): The callback that will be called after fetch_article_cb_freq articles have been queried. Defaults to None.
            fetch_article_cb_freq (int, optional): The frequency of calling fetch_article_cb. Defaults to 100.
            classify_data_cb (Callable[[int, float], None], optional): The callback that will be called after classify_data_cb_freq articles have been classified. Defaults to None.
            classify_data_cb_freq (int, optional): The frequency of calling classify_data_cb_freq. Defaults to 100.
            finished_execution_cb (Callable[[], None], optional): The callback to be called once the query has successfully finished. Defaults to None.

        Raises:
            InvalidTimeRangeError: Raised when timerange is invalid iff end_date < start_date
        """
        # Change to Paper Scraper Queries
        if start_execution_cb is not None:
            start_execution_cb()

        unknown_date_ranges = get_unknown_date_ranges(query)

        with self.issn_database as db:
            issns = {name: db.get_issn_from_name(name)
                     for name in query.journals_to_query}

        g_query_id: Iterator[int] = itertools.count()

        # Convert the User Query into PaperScraper Queries
        queries = self._convert_user_to_paper_scraper_query(issns, g_query_id,
                                                            unknown_date_ranges)

        # DELEGATE ALL QUERIES and handle them accordingly
        scraped_articles = \
            self._scrape_queries_with_paperscraper(queries,
                                                   g_query_id,
                                                   fetch_article_cb,
                                                   fetch_article_cb_freq)

        # Now that we have all queries use the ML Model to judge them and
        # store them as Article_DB_Format
        scraped_articles_db_format = []
        classifier = MlModelWrapper()
        cnt = 0

        #scraped_articles = [Response(1, ArticleMetadata(title="Lower land use intensity promoted soil macrofaunal biodiversity on a reclaimed coast after land use conversion",
        #                                    authors="Boping Tang;Baoming Ge;Yang Li;Senhao Jiang;Jing Zhou;Yang Ruiping",
        #                                    abstract="Abstract Land reclamation is a practice that dates back thousands of years, due to population growth and social development over time. In the past, reclaimed lands were mainly used as croplands with intensive land use. In recent decades, conversion to lower-intensity use has occurred, such as on the coast of China. Here, we selected a study area that was reclaimed approximately 100 years ago on the coast of the Yellow Sea, Jiangsu, China. We identified different land uses: paddy, upland, upland-forest, forest, and vegetable garden. Land use intensity was assigned and scored by input and output indicators. Macrofaunal communities and soil properties were analyzed to detect variations among habitats. The structural and functional composition of the soil macrofaunal community varied significantly with soil properties. After the cropland was converted to forest, the biodiversity indices increased and the soil macrofaunal community became more complex, with expanding groups of detritivores and predators. However, trends observed among herbivores and omnivores did not vary significantly. The highest salinity and bulk density were found in the forest. The highest nutrient contents, such as soil organic carbon, total nitrogen, and total phosphorous, were found in the vegetable garden. Higher soil moisture content was found in the forest and vegetable garden. Soil moisture was identified as the key soil property in shaping the soil macrofaunal community. Furthermore, soil moisture and salinity were selected in the optimal regression models for explaining the measured parameters of soil macrofaunal communities, including taxonomic richness, density, Shannon index, and Margalef index. Variations in the soil macrofaunal community should be regarded as a comprehensive response to the changes in soil properties co-varying with land use conversion. Our findings indicated that land use conversion with lower land use intensity increased soil macrofaunal biodiversity at the reclaimed coast.",
        #                                    journal_name="Agriculture, Ecosystems & Environment"))]

        for response in scraped_articles:
            article = response.metadata
            relevant = False
            cnt = cnt + 1
            if article.abstract is not None and article.abstract != "":
                relevant = classifier.predict_article(article)


            scraped_articles_db_format.append(
                map_to_db_metadata(article, relevant)
            )

            if cnt > classify_data_cb_freq and classify_data_cb is not None:
                classify_data_cb(len(scraped_articles_db_format),
                                 len(scraped_articles_db_format) /
                                 len(scraped_articles))
                cnt = 0

        classify_data_cb(len(scraped_articles_db_format), 1)

        with ArticleRepositoryAPI(self.article_database) as db:
            for article in scraped_articles_db_format:
                db.store_article(article)

        with PrevQueryInformation() as db:
            for name, ranges in unknown_date_ranges.items():
                for range in ranges:
                    db.insert_successful_query(issns[name], range)
                db.merge_ranges(issns[name])

        if finished_execution_cb is not None:
            finished_execution_cb()

    @staticmethod
    def _scrape_queries_with_paperscraper(queries: List[ISSNTimeIntervalQuery], query_id: Iterator[int],
                                          fetch_article_cb: Optional[Callable[[int, float], None]],
                                          fetch_article_cb_freq: int):
        """Delegates all queries using the Paperscraper.

        Args:
            queries (List[ISSNTimeIntervalQuery]): The queries to process
            query_id (Iterator[int]): A query_id generator
            fetch_article_cb (Optional[Callable[[int, float], None]]): A callback to call after fetch_article_cb_freq iterations or none.
            fetch_article_cb_freq (int): The frequency of the calling of the callback.

        Returns:
            List[Response]: The scraped articles.
        """

        random.shuffle(queries)
        scraped_articles = []
        cnt = 0
        tot = len(queries)
        sum = 0
        num = 0
        with PaperScraper() as ps:
            for query in queries:
                ps.delegate_query(query)
            while not ps.processed_all_queries:
                response = ps.poll_response()

                if isinstance(response, FailedQueryResponse):
                    continue
                elif isinstance(response, JournalDaterangeResponse):
                    articles_w_abstract = \
                        [article for article in response.all_articles if
                         article.abstract is not None and article.abstract != ""]
                    articles_wo_abstract = \
                        [article for article in response.all_articles if
                         article.abstract is None or article.abstract == ""]

                    # scraped_articles.extend(articles_w_abstract)
                    cnt += len(articles_w_abstract)
                    num += 1
                    sum += len(articles_w_abstract) + len(articles_wo_abstract)
                    for article in articles_wo_abstract:
                        if article.doi is not None and article.doi != "":
                            q = DoiQuery(next(query_id), article.doi)
                            q.add_journal_data(
                                JournalData(
                                    publication_date=article.publication_date,
                                    journal_name=article.journal_name,
                                    journal_issue=article.journal_issue,
                                    journal_volume=article.journal_volume,
                                    issn=article.issn
                                ))
                            ps.delegate_query(q)
                        else:
                            q = KeywordQuery(next(query_id),
                                             article.authors,
                                             article.title,
                                             article.journal_name)
                            q.add_journal_data(
                                JournalData(
                                    publication_date=article.publication_date,
                                    journal_name=article.journal_name,
                                    journal_issue=article.journal_issue,
                                    journal_volume=article.journal_volume,
                                    issn=article.issn))
                            ps.delegate_query(q)

                elif isinstance(response, Response):
                    cnt = cnt + 1
                    scraped_articles.append(response)

                if cnt >= fetch_article_cb_freq \
                        and fetch_article_cb is not None:
                    num_scraped = len(scraped_articles)
                    est = min(1.0, num_scraped / (tot * sum / num)) if num > 0 \
                        else 0
                    est = max(est, 0.01)
                    fetch_article_cb(num_scraped, est)
                    cnt = 0

        if fetch_article_cb is not None:
            fetch_article_cb(len(scraped_articles), 1.0)

        return scraped_articles

    @staticmethod
    def _convert_user_to_paper_scraper_query(issns: Dict[str, str], query_id_generator: Iterator[int],
                                             unknown_date_ranges: Dict[str, Set[Daterange]]) -> List[
        ISSNTimeIntervalQuery]:
        """Converts user queries to PaperScraper queries and divides every daterange into at most 180 day intervals.

        Args:
            issns (Dict[str, str]): A map from names to issns.
            query_id_generator (Generator[int, None, None]): Generator that creates new query_ids.
            unknown_date_ranges (Dict[str, Set[Daterange]]): A dictionary of unknown date ranges that are mappings from names to a set of dateranges.

        Returns:
            List[ISSNTimeIntervalQuery]: All ISSNTimeIntervalQueries we need to perform.
        """
        queries = []
        for name, ranges in unknown_date_ranges.items():
            issn = issns[name]
            for rnge in ranges:
                delta = rnge.end_date - rnge.start_date
                days = delta.days
                # SPLIT INTO BLOCKS OF AT MOST 3 months
                count = 0
                split = int(math.ceil(days / 360.0))
                step = days // split

                while True:
                    start = rnge.start_date + timedelta(days=count * step)
                    end = min(
                        rnge.start_date + timedelta(days=(count + 1) * step),
                        rnge.end_date)

                    queries.append(
                        ISSNTimeIntervalQuery(next(query_id_generator), issn,
                                              start, end))
                    count = count + 1
                    if end >= rnge.end_date:
                        break
        return queries
