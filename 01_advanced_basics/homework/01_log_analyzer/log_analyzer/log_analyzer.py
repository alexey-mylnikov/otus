#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import json
import copy
import gzip
import sqlite3
import logging
import argparse
import datetime
from collections import namedtuple
from patterns import ui_log_file_name_re, ui_log_string_re

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
}


# TODO: to_json()
class Request(object):
    __slots__ = ['url', 'count', 'count_perc', 'time_sum',
                 'time_perc', 'time_avg', 'time_max', 'time_med']

    def __init__(self, url, count, count_perc, time_sum,
                 time_perc, time_avg, time_max, time_med):

        self.url = url
        self.count = count
        self.count_perc = count_perc
        self.time_sum = time_sum
        self.time_perc = time_perc
        self.time_avg = time_avg
        self.time_max = time_max
        self.time_med = time_med


class Median(object):
    def __init__(self):
        self.row = []

    def step(self, value):
        self.row.append(value)

    def finalize(self):
        length = len(self.row)
        row = sorted(self.row)

        if length % 2:
            return (row[length / 2 - 1] + row[length / 2]) / 2.0
        else:
            return row[length / 2]


def find_latest(catalog, sample, date_format):
    File = namedtuple('File', ['path', 'extension', 'date'])
    latest_file, latest_dt = None, None

    for root, __, files in os.walk(catalog):
        for file_name in files:
            match = sample.match(file_name)
            if match:
                dt = datetime.datetime.strptime(match.group('date'), date_format)
                if not latest_dt or latest_dt < dt:
                    latest_dt = dt
                    latest_file = File(
                        path=os.path.join(root, file_name),
                        extension=match.group('extension'),
                        date=dt
                    )

    return latest_file


def parse_log(file_path, pattern, compressed=False):
    opener = gzip.open if compressed else open

    with opener(file_path, 'rb') as lf:
        for line in lf:
            match = pattern.match(line)
            if match:
                url, request_time = match.group('url'), match.group('request_time')
            else:
                url, request_time = None, 0.0
            yield url, request_time


def init_db(db=None):
    database = db if db else ":memory:"
    conn = sqlite3.connect(database)
    conn.create_aggregate('median', 1, Median)
    conn.execute('CREATE TABLE requests (url TEXT, request_time REAL)')
    return conn


def fill_table(conn, requests):
    with conn:
        conn.executemany("INSERT INTO requests (url, request_time) VALUES (?, ?)", requests)


def aggregate_table(conn):
    curs = conn.cursor()
    curs.execute("SELECT COUNT(*) FROM requests")
    total_count = curs.fetchone()[0]

    curs.execute("SELECT COUNT(*) FROM requests WHERE url IS NULL")
    errors_count = curs.fetchone()[0]

    # TODO: errors perc

    curs.execute("SELECT SUM(request_time) FROM requests")
    total_time_sum = curs.fetchone()[0]

    query = """SELECT url, 
                      COUNT(*), 
                      SUM(request_time), 
                      AVG(request_time), 
                      MAX(request_time), 
                      MEDIAN(request_time) FROM requests GROUP BY url ORDER BY request_time DESC"""

    for url, count, time_sum, time_avg, time_max, time_med in conn.execute(query):
        count_perc = (count / total_count) * 100
        time_perc = (time_sum / total_time_sum) * 100
        yield Request(url, count, count_perc, time_sum, time_perc, time_avg, time_max, time_med)


def main(**kwargs):
    log_file = find_latest(
        catalog=kwargs.get('LOG_DIR'),
        sample=ui_log_file_name_re,
        date_format=kwargs.get('LOG_FILE_DATE_FORMAT', '%Y%m%d')
    )

    if not log_file:
        logging.info('no files to process')
        return

    report_file = os.path.join(kwargs.get('REPORT_DIR'), 'report-{:%Y.%m.%d}.html'.format(log_file.date))

    if os.path.exists(report_file):
        logging.info('latest logs already analyzed, see {}'.format(report_file))
        return

    conn = init_db()

    requests = parse_log(
        file_path=log_file.path,
        pattern=ui_log_string_re,
        compressed=(log_file.extension == '.gz')
    )

    fill_table(conn, requests)

    test = [request for request in aggregate_table(conn)]

    conn.close()


class ConfigAction(argparse.Action):
    def __call__(self, arg_parser, namespace, value, option_string=None):
        if not (os.path.exists(value) or os.path.isfile(value)):
            raise argparse.ArgumentError(self, 'must be an existing file')

        default_config = copy.deepcopy(getattr(namespace, self.dest))

        with open(value, 'r') as cf:
            try:
                custom_config = json.load(cf)
            except ValueError as e:
                raise argparse.ArgumentError(self, 'must be valid json file\n {}'.format(e))

        default_config.update(custom_config)
        setattr(namespace, self.dest, default_config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default=config, action=ConfigAction, help='json config file')
    parser.add_argument('-l', '--log', default=None, help='log file')
    args, __ = parser.parse_known_args()

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
        stream=sys.stdout
    )

    main(**args.config)
