FROM python:2.7-alpine

RUN apk upgrade --update --no-cache && \
	apk add --update --no-cache \
		acl \
		bash \
		ca-certificates \
		shadow \
		sudo

COPY app /opt/app/
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
WORKDIR /opt/app
