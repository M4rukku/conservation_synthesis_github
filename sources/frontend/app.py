from datetime import datetime

import pandas as pd
from flask import Flask, render_template, request

from sources.data_controller.controller_interface import \
    DatabaseResultQueryHandler
from sources.data_controller.controller_interface import UserQueryHandler
from sources.frontend.user_queries import ResultFilter
from sources.frontend.user_queries import UserQueryInformation

app = Flask(__name__)

# mock up content for the journals
def get_journals():
    # read in the frequency value, notice the relative path
    table = pd.read_json("frontend_data/journal_usage_frequency.pd.json")
    table.sort_values(by='counts',ascending=False,inplace=True)
    journal_list = table.index.tolist()
    # remove empty list
    journal_list = [x for x in journal_list if x]
    return journal_list

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    return render_template('search.html', journal_name = get_journals(), topic = "Publication")

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
    return render_template('results.html', journal_name = get_journals(), topic = "Sync")

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
    start_date = request.form['start_date']
    start_date_object = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = request.form['end_date']
    end_date_object = datetime.strptime(end_date, '%Y-%m-%d').date()
    # create result filter object
    result_filter = ResultFilter(journal_names=journals,
                              relevant_only=relevant_only,
                              from_sync_date=start_date_object,
                              to_sync_date=end_date_object)
    # create query handler and process query
    filter_handler = DatabaseResultQueryHandler()
    filter_handler.process_filter_query(result_filter)
    return results()

@app.route('/sync')
def sync():
    return render_template('sync.html')

#run flask under debug mode for development
if __name__ == '__main__':
    app.run(debug=True)