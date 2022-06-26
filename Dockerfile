FROM python:3.7-slim

COPY requirements.txt .

RUN pip3 install -r requirements.txt
COPY *.py ./
CMD python ./api.py
