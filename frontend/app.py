from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

#mock up content for the journals
def get_journals():
    #read in the frequency value, notice the relative path
    table = pd.read_json("../data/journal_data/journal_usage_frequency.pd.json")
    table.sort_values(by='counts',ascending=False,inplace=True)
    journal_list = table.index.tolist()
    #remove empty list
    journal_list = [x for x in journal_list if x]
    return journal_list

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    return render_template('search.html',journal_name = get_journals())

@app.route('/handle-query', methods=['POST'])
def handle_query():
    if request.form.get('relevant_only'):
        print("yes relevant")
    if request.form.get('all_journals'):
        print("yes journals")
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    print(start_date)
    print(end_date)
    return search()

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/sync')
def sync():
    return render_template('sync.html')

#run flask under debug mode for development
app.run(debug=True)