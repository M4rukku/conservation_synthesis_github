from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import Flask, render_template, request

from sources.data_controller.controller_interface import \
    DatabaseResultQueryHandler
from sources.data_controller.controller_interface import UserQueryHandler
from sources.frontend.user_queries import ResultFilter
from sources.frontend.user_queries import UserQueryInformation

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

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
    path = Path(__file__) / "frontend_data" / "journal_usage_frequency.pd.json"
    table = pd.read_json(path)
    table.sort_values(by='counts',ascending=False,inplace=True)
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
    start_date_object = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = request.form['end_date']
    end_date_object = datetime.strptime(end_date, '%Y-%m-%d')
    # create user query object
    user_query = UserQueryInformation(journals, start_date_object, end_date_object, relevant_only)
    # create query handler and process query
    user_query_handler = UserQueryHandler()
    user_query_handler.process_user_query(user_query)
    return search()

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
    return render_template('results.html', journal_name = get_journals(), topic = "Sync", display_table=False, result=None, dates=dates, criteria=criteria)

@app.route('/results-table')
def results_table(filter_result):
    return render_template('results.html', journal_name = get_journals(), topic = "Sync", display_table=True, result=filter_result)

# handle query input on the results page
@app.route('/handle-results-query', methods=['POST'])
def handle_results_query():
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
    start_date_object = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = request.form['end_date']
    end_date_object = datetime.strptime(end_date, '%Y-%m-%d')
    # create result filter object
    result_filter = ResultFilter(journal_names=journals,
                              relevant_only=relevant_only,
                              from_pub_date=start_date_object,
                              to_pub_date=end_date_object,
                              sync_date=sync_date_object,)
    # create query handler and process query
    filter_handler = DatabaseResultQueryHandler()
    result = filter_handler.process_filter_query(result_filter)
    list_of_result_dicts = convert_result(result)
    return results_table(list_of_result_dicts)

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


@app.route('/sync')
def sync():
    return render_template('sync.html')

#run flask under debug mode for development
if __name__ == '__main__':
    app.run(debug=True)