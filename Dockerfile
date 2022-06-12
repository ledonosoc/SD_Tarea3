FROM python:3.7-slim

RUN pip3 install -U cassandra-driver
COPY *.py ./
CMD python ./main.py
