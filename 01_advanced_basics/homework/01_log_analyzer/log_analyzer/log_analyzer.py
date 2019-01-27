#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import json
import copy
import gzip
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
    "LOG_FILE_DATE_FORMAT": "%Y%m%d"
}


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


def parse_log(file_path, pattern, compressed=False, groups=None):
    opener = gzip.open if compressed else open
    method, arguments = ('group', groups) if groups else ('groups', [])

    with opener(file_path, 'rb') as lf:
        for line in lf:
            match = pattern.match(line)
            yield getattr(match, method)(*arguments) if match else None


def get_request_time_statistics(file_path, compressed):
    requests = parse_log(
        file_path=file_path,
        pattern=ui_log_string_re,
        compressed=compressed,
        groups=('url', 'request_time')
    )

    for request in requests:
        if not request:
            continue

        url, time = request
        # url, __, params = url.partition('?')
        # params = dict(param.split('=') for param in params.split('&'))


def main(**kwargs):
    log_file = find_latest(
        catalog=kwargs.get('LOG_DIR'),
        sample=ui_log_file_name_re,
        date_format=kwargs.get('LOG_FILE_DATE_FORMAT')
    )

    if not log_file:
        logging.info('no files to process')
        return

    report_file = os.path.join(kwargs.get('REPORT_DIR'), 'report-{:%Y.%m.%d}.html'.format(log_file.date))

    if os.path.exists(report_file):
        logging.info('latest logs already analyzed, see {}'.format(report_file))
        return

    get_request_time_statistics(
        file_path=log_file.path,
        compressed=(log_file.extension == '.gz')
    )


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
