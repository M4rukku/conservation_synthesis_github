import itertools
import math
import threading

from sources.data_processing.abstract_webscraping import get_abstract_from_doi
from sources.data_processing.paper_scraper_api import PaperScraper
from sources.data_processing.queries import ISSNTimeIntervalQuery, Response, \
    JournalDaterangeResponse, FailedQueryResponse, DoiQuery, KeywordQuery, \
    ArticleMetadata
from sources.databases.article_data_db import MariaRepositoryAPI, \
    DBArticleMetadata
from sources.databases.daterange_util import Daterange, DaterangeUtility
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

    for name, range in query_ranges:
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
                             relevant=relevant)


class QueryDispatcher:
    def __init__(self):
        pass

    def process_query(self, query: UserQueryInformation) -> UserQueryResponse:
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
            args=(query, unknown_date_ranges))

        thread.daemon = True
        thread.start()

        response = []
        with MariaRepositoryAPI() as db:
            for name in query.journals_to_query:
                response.append(
                    db.general_query(name,
                                     query.start_date_range,
                                     query.end_date_range,
                                     query.relevant_only,
                                     query.classification_restriction))
        missing_information = \
            [name + " Missing Ranges: \n" + "   ".join(map(str, ls_date_range))
             for name, ls_date_range in unknown_date_ranges]

        missing_information = "\n\n".join(missing_information)

        return \
            UserQueryResponse(response,
                              f"Missing Information: {missing_information}")

    def _load_and_synchronize_in_background(self, query:
    UserQueryInformation, unknown_date_ranges):
        # Change to Paper Scraper Queries

        with JournalNameIssnDatabase() as db:
            issns = {name: db.get_issn_from_name(name)
                     for name in query.journals_to_query}

        queries = []
        query_id = itertools.count()

        # Convert the User Query into PaperSCraper Queries
        for name, ranges in unknown_date_ranges:
            issn = issns[name]
            for rnge in ranges:
                delta = rnge.end_date - rnge.start_date
                days = delta.days
                # SPLIT INTO BLOCKS OF AT MOST 3 months
                count = 0
                split = int(math.ceil(days / 90.0))
                step = days / split

                while True:
                    start = rnge.start_date + count * step
                    end = min(rnge.start_date + (count + 1) * step,
                              rnge.end_date)

                    queries.append(
                        ISSNTimeIntervalQuery(next(query_id), issn, start, end))

                    count = count + 1
                    if end >= rnge.end_date:
                        break

        # DELEGATE ALL QUERIES and handle them accordingly
        scraped_articles = []
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

                    scraped_articles.extend(articles_w_abstract)

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
                    if response.metadata.abstract is not None and \
                            response.metadata.abstract != "":
                        scraped_articles.append(response.metadata)
                    else:
                        doi = response.metadata.doi
                        if article.doi is not None and article.doi != "":
                            abstract = get_abstract_from_doi(doi)
                            response.metadata.abstract = abstract
                            scraped_articles.append(response.metadata)
                        else:
                            scraped_articles.append(response.metadata)

        # Now that we have all queries use the ML Model to judge them and
        # store them as Article_DB_Format
        scraped_articles_db_format = []
        classifier = MlModelWrapper()
        for article in scraped_articles:
            relevant = False
            if article.abstract is not None and article.abstract != "":
                relevant = classifier.predict_article(article)
            scraped_articles_db_format.append(
                map_to_db_metadata(article, relevant)
            )

        with MariaRepositoryAPI() as db:
            for article in scraped_articles_db_format:
                db.store_article(article)

        with PrevQueryInformation() as db:
            for name, ranges in unknown_date_ranges:
                for range in ranges:
                    db.insert_successful_query(issns[name], range)
                db.merge_ranges(issns[name])
