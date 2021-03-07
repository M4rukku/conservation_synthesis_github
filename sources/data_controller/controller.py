import datetime
import itertools
import math
import threading
from datetime import timedelta

from sources.data_processing.abstract_webscraping import get_abstract_from_doi
from sources.data_processing.paper_scraper_api import PaperScraper
from sources.data_processing.queries import ISSNTimeIntervalQuery, Response, \
    JournalDaterangeResponse, FailedQueryResponse, DoiQuery, KeywordQuery, \
    ArticleMetadata
from sources.databases.article_data_db import ArticleRepositoryAPI, \
    DBArticleMetadata
from sources.databases.daterange_util import Daterange, DaterangeUtility
from sources.databases.internal_databases import SQLiteDB, InternalSQLDatabase
from sources.databases.journal_name_issn_database import JournalNameIssnDatabase
from sources.databases.prev_query_information_db import PrevQueryInformation
from sources.frontend.user_queries import UserQueryResponse, \
    UserQueryInformation
from sources.ml_model.ml_model import MlModelWrapper


class InvalidTimeRangeError(Exception):
    pass


def get_unknown_date_ranges(query: UserQueryInformation):
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
    def __init__(self,
                 issn_database: JournalNameIssnDatabase = None,
                 article_database: InternalSQLDatabase = None):

        self.issn_database = \
            JournalNameIssnDatabase if issn_database is None else issn_database
        self.article_database = SQLiteDB() if issn_database is None else \
            article_database

    def process_query(self, query: UserQueryInformation,
                      fetch_article_cb, fetch_article_cb_freq,
                      classify_data_cb, classify_data_cb_freq,
                      finished_execution_cb) -> UserQueryResponse:

        """ Processes a user query instantly! Returns what is known so far,
        and tells the user that the rest will be loaded in the future

        :param query: A UserQueryInformation object
        """

        # Check Validity of Daterange
        if query.end_date_range <= query.start_date_range:
            raise InvalidTimeRangeError

        unknown_date_ranges = get_unknown_date_ranges(query)

        # Dispatch the unknown ranges to be queried in the bg
        thread = threading.Thread(
            target=self._load_and_synchronize_in_background,
            args=(query, unknown_date_ranges,
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
                                            unknown_date_ranges,
                                            fetch_article_cb,
                                            fetch_article_cb_freq,
                                            classify_data_cb,
                                            classify_data_cb_freq,
                                            finished_execution_cb):
        # Change to Paper Scraper Queries

        with self.issn_database() as db:
            issns = {name: db.get_issn_from_name(name)
                     for name in query.journals_to_query}

        g_query_id = itertools.count()

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
                                 len(scraped_articles_db_format)/
                                 len(scraped_articles))
                cnt = 0

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
    def _scrape_queries_with_paperscraper(queries, query_id,
                                          fetch_article_cb,
                                          fetch_article_cb_freq):
        scraped_articles = []
        cnt = 0
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

                    for article in articles_wo_abstract:
                        if article.doi is not None and article.doi != "":
                            ps.delegate_query(
                                DoiQuery(next(query_id), article.doi))
                        else:
                            ps.delegate_query(
                                KeywordQuery(next(query_id),
                                             article.authors,
                                             article.title,
                                             article.journal_name))

                elif isinstance(response, Response):
                    cnt = cnt + 1
                    if response.metadata.abstract is not None and \
                            response.metadata.abstract != "":
                        scraped_articles.append(response)
                    else:
                        doi = response.metadata.doi
                        if article.doi is not None and article.doi != "":
                            abstract = get_abstract_from_doi(doi)
                            response.metadata.abstract = abstract
                            scraped_articles.append(response)
                        else:
                            scraped_articles.append(response)

                if cnt >= fetch_article_cb_freq \
                        and fetch_article_cb is not None:
                    num_scraped = len(scraped_articles)
                    fetch_article_cb(num_scraped,
                                     num_scraped / (num_scraped +
                                                    ps.delegation_qsize()))
                    cnt = 0

        if fetch_article_cb is not None:
            fetch_article_cb(len(scraped_articles), 1.0)

        return scraped_articles

    @staticmethod
    def _convert_user_to_paper_scraper_query(issns, query_id_generator,
                                             unknown_date_ranges):
        queries = []
        for name, ranges in unknown_date_ranges.items():
            issn = issns[name]
            for rnge in ranges:
                delta = rnge.end_date - rnge.start_date
                days = delta.days
                # SPLIT INTO BLOCKS OF AT MOST 3 months
                count = 0
                split = int(math.ceil(days / 90.0))
                step = days // split

                while True:
                    start = rnge.start_date + timedelta(days=count * step)
                    end = min(
                        rnge.start_date + timedelta(days=(count + 1) * step),
                        rnge.end_date)

                    queries.append(
                        ISSNTimeIntervalQuery(next(query_id_generator), issn,
                                              start.date(), end.date()))
                    count = count + 1
                    if end >= rnge.end_date:
                        break
        return queries
