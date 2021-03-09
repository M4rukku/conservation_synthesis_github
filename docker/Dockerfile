FROM nvcr.io/nvidia/pytorch:21.02-py3
COPY ./requirements.txt /app
RUN pip3 install -r /app/requirements.txt
CMD ["flask", "run"]