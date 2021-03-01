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

The app should run at http://127.0.0.1:5000/.
