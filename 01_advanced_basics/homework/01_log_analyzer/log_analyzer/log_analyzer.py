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
from string import Template
from collections import namedtuple
from decorators import catcher
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


@catcher(logger=logging)
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


@catcher(logger=logging)
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


@catcher(logger=logging)
def init_db(db=None):
    database = db if db else ":memory:"
    conn = sqlite3.connect(database)
    conn.create_aggregate('median', 1, Median)
    conn.execute('CREATE TABLE requests (url TEXT, request_time REAL)')
    return conn


@catcher(logger=logging)
def close_conn(conn):
    conn.close()


def fill_requests_table(conn, data):
    with conn:
        conn.executemany("INSERT INTO requests (url, request_time) VALUES (?, ?)", data)


def get_requests_count(conn):
    curs = conn.cursor()
    curs.execute("SELECT COUNT(*) FROM requests")
    return curs.fetchone()[0]


def get_errors_count(conn):
    curs = conn.cursor()
    curs.execute("SELECT COUNT(*) FROM requests WHERE url IS NULL")
    return curs.fetchone()[0]


def get_total_time_sum(conn):
    curs = conn.cursor()
    curs.execute("SELECT SUM(request_time) FROM requests")
    return curs.fetchone()[0]


def get_requests_stats(conn, limit=None):
    query = """SELECT url, 
                      COUNT(*), 
                      SUM(request_time), 
                      AVG(request_time), 
                      MAX(request_time), 
                      MEDIAN(request_time) FROM requests GROUP BY url ORDER BY 3 DESC"""

    if limit:
        query += ' LIMIT {}'.format(limit)

    for stat in conn.execute(query):
        yield stat


@catcher(logger=logging)
def aggr_requests_stat(conn, data, error_threshold, limit=None):
    fill_requests_table(conn, data)
    total_count = get_requests_count(conn)
    errors_count = get_errors_count(conn)

    if ((errors_count / total_count) * 100) > error_threshold:
        raise RuntimeError('error threshold exceeded')

    total_time_sum = get_total_time_sum(conn)
    stats = []

    for url, count, time_sum, time_avg, time_max, time_med in get_requests_stats(conn, limit):
        stats.append(
            {
                'url': url,
                'count': count,
                'time_sum': time_sum,
                'time_avg': time_avg,
                'time_max': time_max,
                'time_med': time_med,
                'time_perc': (time_sum / total_time_sum) * 100,
                'count_perc': (count / total_count) * 100
            }
        )

    return stats


@catcher(logger=logging)
def render_template(src, dst, data):
    with open(src, 'r') as sf:
        template = sf.read()

    with open(dst, 'w') as df:
        df.write(Template(template).safe_substitute(data))


def main(**kwargs):
    log_file = find_latest(
        catalog=kwargs.get('LOG_DIR'),
        sample=ui_log_file_name_re,
        date_format='%Y%m%d'
    )

    if not log_file:
        logging.info('no files to process')
        return

    report_template = os.path.join(kwargs.get('REPORT_DIR'), 'report.html')
    report = os.path.join(kwargs.get('REPORT_DIR'), 'report-{:%Y.%m.%d}.html'.format(log_file.date))

    assert os.path.exists(report_template), 'report template not found'

    if os.path.exists(report):
        logging.info('latest logs already analyzed, see {}'.format(report))
        return

    conn = init_db()

    log = parse_log(
        file_path=log_file.path,
        pattern=ui_log_string_re,
        compressed=(log_file.extension == '.gz')
    )

    stat = aggr_requests_stat(
        conn=conn,
        data=log,
        error_threshold=kwargs.get('ERROR_THRESHOLD', 50),
        limit=kwargs.get('REPORT_SIZE')
    )

    render_template(
        src=report_template,
        dst=report,
        data={'table_json': stat}
    )

    close_conn(conn)


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
