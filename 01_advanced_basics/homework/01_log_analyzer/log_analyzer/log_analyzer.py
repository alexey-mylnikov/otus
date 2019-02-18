#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import copy
import gzip
import shutil
import sqlite3
import logging
import argparse
import datetime
import tempfile
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


@catcher(logger=logging)
def find_latest(catalog, sample, date_format):
    File = namedtuple('File', ['path', 'extension', 'date'])
    latest_file, latest_dt = None, None
    regexp = re.compile(sample)

    for root, __, files in os.walk(catalog):
        for file_name in files:
            match = regexp.match(file_name)
            if match:
                dt, extension = match.group('date'), match.group('extension')
                dt = datetime.datetime.strptime(dt, date_format)

                if not latest_dt or latest_dt < dt:
                    latest_dt = dt
                    latest_file = File(
                        path=os.path.join(root, file_name),
                        extension=extension,
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
                url, request_time = None, '0.0'
            yield url, request_time


class Median(object):
    def __init__(self):
        self.row = []

    def step(self, value):
        self.row.append(value)

    def finalize(self):
        length = len(self.row)
        row = sorted(self.row)

        if length % 2:
            return row[length / 2]
        else:
            return (row[length / 2 - 1] + row[length / 2]) / 2.0


class SQLiteFactory(sqlite3.Connection):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()


def connect_to_db():
    conn = sqlite3.connect(":memory:", factory=SQLiteFactory)
    conn.create_aggregate('median', 1, Median)
    conn.text_factory = str
    conn.execute('CREATE TABLE requests (url TEXT, request_time REAL)')

    return conn


def fill_table(conn, data):
    conn.executemany("INSERT INTO requests (url, request_time) VALUES (?, ?)", data)


def get_requests_count(conn):
    curs = conn.cursor()
    curs.execute("SELECT COUNT(*) FROM requests")
    result = curs.fetchone()
    curs.close()
    return result[0]


def get_errors_count(conn):
    curs = conn.cursor()
    curs.execute("SELECT COUNT(*) FROM requests WHERE url IS NULL")
    result = curs.fetchone()
    curs.close()
    return result[0]


def get_total_time(conn):
    curs = conn.cursor()
    curs.execute("SELECT SUM(request_time) FROM requests")
    result = curs.fetchone()
    curs.close()
    return result[0]


def get_requests_stats(conn, limit=None):
    query = """SELECT url, 
                      COUNT(*), 
                      SUM(request_time), 
                      AVG(request_time), 
                      MAX(request_time), 
                      MEDIAN(request_time)
                      FROM requests GROUP BY url ORDER BY 3 DESC"""

    if limit:
        query += ' LIMIT {}'.format(limit)

    for stat in conn.execute(query):
        yield stat


def aggr_requests_stat(stat, total_time, total_count):
    stats = []

    for url, count, time_sum, time_avg, time_max, time_med in stat:
        stats.append(
            {
                'url': url,
                'count': count,
                'time_sum': round(time_sum, 3),
                'time_avg': round(time_avg, 3),
                'time_max': round(time_max, 3),
                'time_med': round(time_med, 3),
                'time_perc': round(time_sum * 100.0 / total_time, 3),
                'count_perc': round(count * 100.0 / total_count, 3)
            }
        )

    return stats


def render_template(src, dst, data):
    with open(src, 'r') as sf:
        template = sf.read()

    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(Template(template).safe_substitute(data))

    shutil.copyfile(tf.name, dst)
    os.unlink(tf.name)


@catcher(logger=logging)
def main(**kwargs):
    work_dir = os.path.abspath(os.path.dirname(__file__))

    log_file = find_latest(
        catalog=kwargs.get('LOG_DIR', work_dir),
        sample=ui_log_file_name_re,
        date_format='%Y%m%d'
    )

    if not log_file:
        logging.info('no files to process')
        return

    logging.info('analysing file: {}'.format(log_file.path))

    template = os.path.join(
        kwargs.get('REPORT_DIR', os.path.join(work_dir, 'reports')),
        'report.html'
    )
    report = os.path.join(
        kwargs.get('REPORT_DIR', os.path.join(work_dir, 'reports')),
        'report-{:%Y.%m.%d}.html'.format(log_file.date)
    )

    assert os.path.exists(template), 'report template not found'

    if os.path.exists(report):
        logging.info('latest logs already analyzed, see {}'.format(report))
        return

    compressed = log_file.extension == '.gz'
    data = parse_log(file_path=log_file.path, pattern=ui_log_string_re, compressed=compressed)

    with connect_to_db() as conn:
        fill_table(conn=conn, data=data)
        total_count = get_requests_count(conn)
        total_time = get_total_time(conn)
        errors_count = get_errors_count(conn)

        errors_perc = errors_count * 100.0 / total_count
        threshold = kwargs.get('ERROR_THRESHOLD', 50)
        assert errors_perc < threshold, 'could not parse more than {}% of logs'.format(threshold)

        stat = get_requests_stats(conn=conn, limit=kwargs.get('REPORT_SIZE'))
        aggr = aggr_requests_stat(stat=stat, total_time=total_time, total_count=total_count)

    render_template(src=template, dst=report, data={'table_json': json.dumps(aggr)})
    logging.info('done. report: {}'.format(report))
    return report


class ParseConfigAction(argparse.Action):
    def __call__(self, arg_parser, namespace, value, option_string=None):
        if not (os.path.exists(value) and os.path.isfile(value)):
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
    parser.add_argument('-c', '--config', default=config, action=ParseConfigAction, help='json config file')
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
