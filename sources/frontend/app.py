import math
from datetime import datetime, date
from pathlib import Path

import pandas as pd
from flask import Flask, render_template, request
from flask_socketio import SocketIO

from sources.data_controller.controller_interface import \
    DatabaseResultQueryHandler
from sources.data_controller.controller_interface import UserQueryHandler
from sources.frontend.user_queries import ResultFilter
from sources.frontend.user_queries import UserQueryInformation

app = Flask(__name__)
app.config['SECRET_KEY'] = "'secret!'"
app.config['DEBUG'] = True
socketio = SocketIO(app)


# display about page
@app.route('/')
def index():
    return render_template('index.html')


# display search query form
@app.route('/search')
def search():
    dates = {
        'start_date': 'Publication Start',
        'end_date': 'Publication End'
    }
    criteria = {
        'relevant_only': 'Return relevant articles only',
        'all_journals': 'Search all journals'
    }
    return render_template('search.html', journal_name=get_journals(), dates=dates, criteria=criteria)


# mock up content for the journals
def get_journals():
    # read in the frequency value, notice the relative path
    path = Path(__file__).parent / "frontend_data" / "journal_usage_frequency.pd.json"
    with path.open("rb") as f:
        table = pd.read_json(f)
    table.sort_values(by='counts', ascending=False, inplace=True)
    journal_list = table.index.tolist()
    # remove empty list
    journal_list = [x for x in journal_list if x]
    return journal_list


# handle query input on the search page
@app.route('/handle-search-query', methods=['POST'])
def handle_search_query():
    # get all form fields
    if request.form.get('relevant_only'):
        relevant_only = True
    else:
        relevant_only = False
    all_journals = get_journals()
    if request.form.get('all_journals'):
        journals = all_journals
    else:
        journals = []
        for journal in all_journals:
            if request.form.get(journal):
                journals.append(journal)
    print(journals)
    start_date = request.form['start_date']
    start_date_object = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = request.form['end_date']
    end_date_object = datetime.strptime(end_date, '%Y-%m-%d').date()
    # create user query object
    user_query = UserQueryInformation(journals, start_date_object, end_date_object, relevant_only)
    # create query handler and process query
    user_query_handler = UserQueryHandler()

    user_query_handler.process_user_query(user_query,
                                          fetch_article_cb_freq=50,
                                          start_execution_cb=start_executation_cb,
                                          classify_data_cb=classify_data_cb,
                                          fetch_article_cb=fetch_article_cb,
                                          finished_execution_cb=finished_execution_cb,
                                          )
    return search()


# display result filter query form
@app.route('/results')
def results():
    dates = {
        'sync_date': 'Sync',
        'start_date': 'Publication Start',
        'end_date': 'Publication End'
    }
    criteria = {
        'relevant_only': 'Return relevant articles only',
        'all_journals': 'Search all journals'
    }
    return render_template('results.html',
                           journal_name=get_journals(),
                           topic="Sync",
                           display_table=False,
                           result=None,
                           dates=dates,
                           criteria=criteria)


global_filter_result = []


# display table of filter results (with pagination)
@app.route('/results-table')
def results_table():
    current_page = request.args.get('page', 1, type=int)
    articles_per_page = 10
    max_page = len(global_filter_result) // articles_per_page + 1
    from_article = (current_page - 1) * articles_per_page
    if current_page == max_page:
        to_article = from_article + (len(global_filter_result) - ((max_page - 1) * articles_per_page))
    else:
        to_article = from_article + articles_per_page
    articles_to_show = global_filter_result[from_article:to_article]
    return render_template('results.html',
                           journal_name=get_journals(),
                           topic="Sync",
                           display_table=True,
                           result=articles_to_show,
                           current_page=current_page,
                           max_page=max_page,
                           articles_per_page=articles_per_page)


# Cache Data so that reloads don't cause an actual reloading of data!
cached_query = None
# True if we are currently responding to a request
in_process = False


# handle query input on the results page
@app.route('/handle-results-query', methods=['POST'])
def handle_results_query():
    #Ensure
    global in_process
    if in_process:
        return
    in_process = True

    # get all form fields
    if request.form.get('relevant_only'):
        relevant_only = True
    else:
        relevant_only = False
    all_journals = get_journals()
    if request.form.get('all_journals'):
        journals = all_journals
    else:
        journals = []
        for journal in all_journals:
            if request.form.get(journal):
                journals.append(journal)
    print(journals)
    sync_date = request.form['sync_date']
    sync_date_object = datetime.strptime(sync_date, '%Y-%m-%d').date()
    start_date = request.form['start_date']
    start_date_object = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = request.form['end_date']
    end_date_object = datetime.strptime(end_date, '%Y-%m-%d').date()
    # create result filter object
    result_filter = ResultFilter(journal_names=journals,
                                 relevant_only=relevant_only,
                                 from_pub_date=start_date_object,
                                 to_pub_date=end_date_object,
                                 from_sync_date=sync_date_object,
                                 to_sync_date=date.today())

    #Ensure we don't double load the same query
    global cached_query
    if cached_query == result_filter:
        in_process = False
        return results_table()
    cached_query = result_filter

    # create query handler and process query
    filter_handler = DatabaseResultQueryHandler()
    result = filter_handler.process_filter_query(result_filter)
    list_of_result_dicts = convert_result(result)
    global global_filter_result
    global_filter_result = list_of_result_dicts
    in_process = False
    return results_table()


# helper function that converts list of objects into dict that can be displayed as a table
def convert_result(result_list):
    list_of_result_dicts = []
    for article in result_list:
        article_dict = {
            "URL": article.url,
            "Title": article.title,
            "Authors": convert_list_to_string(article.authors),
            "Publication Date": article.publication_date,
            "Publisher": article.publisher,
            "Journal Name": article.journal_name,
            "Journal Volume": article.journal_volume,
            "Journal Issue": article.journal_issue,
            "ISSN": article.issn,
            "Sync Date": article.sync_date,
            "Checked?": article.checked,
            "Classified?": article.classified,
            "Relevant?": article.relevant
        }
        list_of_result_dicts.append(article_dict)
    return list_of_result_dicts


# helper function to convert list of authors into one string
def convert_list_to_string(list_of_strings):
    final_string = ''
    for i in range(len(list_of_strings) - 1):
        final_string = final_string + list_of_strings[i] + ', '
    final_string = final_string + list_of_strings[len(list_of_strings) - 1]
    return final_string


# global variables for updating the sync pageSize
download_stats = 0
classification_stats = 0
finished_stats = False


@app.route('/sync')
def sync():
    global finished_stats
    global download_stats
    global classification_stats
    return render_template('sync.html', download_stats=download_stats, classification_stats=classification_stats,
                           finished_stats=finished_stats)


def fetch_article_cb(articles_downloaded_so_far: int, percentage_of_total: float):
    global download_stats
    download_stats = math.trunc(percentage_of_total * 100)
    socketio.emit('download_update', {'download_stats': download_stats}, namespace='/sync')


def classify_data_cb(articles_classified_so_far: int, percentage_of_total: float):
    global classification_stats
    classification_stats = math.trunc(percentage_of_total * 100)
    socketio.emit('classification_update', {'classification_stats': classification_stats}, namespace='/sync')


def finished_execution_cb():
    global finished_stats
    finished_stats = True
    socketio.emit('finished_update', {'finished_stats': finished_stats}, namespace='/sync')


def start_executation_cb():
    global finished_stats
    global download_stats
    global classification_stats
    finished_stats = False
    download_stats = 0
    classification_stats = 0


# run flask under debug mode for development
if __name__ == '__main__':
    socketio.run(app)
