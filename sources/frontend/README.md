# Frontend

## Running Flask App (in dev mode)

Activate a python virtual environment:

```bash
$ python3 -m venv venv
$ source venv/bin/activate
```

Install flask:
```bash
$ pip install flask
```

Set environment variables:
```bash
$ export FLASK_APP=app
$ export FLASK_ENV=development
```

Run app:
```bash
$ flask run
```

## Dashboard Overview

- **About**: start page with short description of tool aim and possibly related links
- **New Search**: configure search (choose papers/APIs to use) and click run button (possibly add functionality that sends email once the search and classification is completed)
- **New Results**: after classification is complete, this will show paper titles(with abstracts and/or links to the papers) with buttons to either accept or reject them as either relevant or not (and correct classifications if wrong?)
- **All Results**: more of a stretch goal but basically UI for the database of already classified papers (maybe with filter system)
