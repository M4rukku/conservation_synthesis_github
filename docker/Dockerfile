FROM nvcr.io/nvidia/pytorch:21.02-py3
COPY .. /app
RUN pip3 install -r /app/requirement_full.txt
ENV FLASK_APP=/app/sources/frontend/app.py
ENV FLASK_RUN_HOST=0.0.0.0
CMD ["flask", "run"]