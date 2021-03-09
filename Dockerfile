FROM nvcr.io/nvidia/pytorch:21.02-py3
COPY ./sources /app
COPY ./requirements.txt /app
RUN pip3 install -r /app/requirements.txt
ENV FLASK_APP=/app/sources/frontend/app.py
ENV FLASK_RUN_HOST=0.0.0.0

#CMD ["flask", "run"]