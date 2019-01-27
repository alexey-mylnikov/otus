FROM python:2.7-alpine

COPY app /opt/app/
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
WORKDIR /opt/app
