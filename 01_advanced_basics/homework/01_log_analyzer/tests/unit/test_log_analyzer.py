#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import gzip
import shutil
import unittest
import argparse
import tempfile
import datetime
import json
from log_analyzer import log_analyzer


def touch(path):
    with open(path, 'a'):
        os.utime(path, None)


class TestParseConfigAction(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, 'config.json')

        self.default = {"REPORT_SIZE": 1000, "REPORT_DIR": "./reports", "LOG_DIR": "./log"}
        self.custom = {"REPORT_SIZE": 10000, "DB_DIR": "./db"}

        with open(self.temp_file, 'wb') as tf:
            json.dump(self.custom, tf)

        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('-c', '--config', default=self.default, action=log_analyzer.ParseConfigAction)

    def test_action_if_config_param_not_set(self):
        args = self.parser.parse_args([])
        self.assertEqual(self.default, args.config, [])

    def test_action_if_config_param_set(self):
        expected = self.default.copy()
        expected.update(self.custom)
        args = self.parser.parse_args(['-c', self.temp_file])
        self.assertEqual(expected, args.config, self.custom)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)


class TestFindLatestLogFile(unittest.TestCase):
    def setUp(self):
        self.date_format = '%Y%m%d'
        self.sample = r'log-(?P<date>\d{8})(?P<extension>\.gz|$)'
        self.temp_dir = tempfile.mkdtemp()

        for log in ('log-20170101.gz', 'log-20170201', 'log-20180201.gz', 'log-20180301'):
            touch(os.path.join(self.temp_dir, log))

        self.latest_path = os.path.join(self.temp_dir, 'log-20181231.gz')
        self.latest_ext = '.gz'
        self.latest_date = datetime.datetime(2018, 12, 31, 0, 0)

        touch(self.latest_path)

    def test_find_latest_log(self):
        args = (self.temp_dir, re.compile(self.sample), self.date_format)
        latest = log_analyzer.find_latest(*args)
        self.assertEqual(self.latest_path, latest.path, args)
        self.assertEqual(self.latest_ext, latest.extension, args)
        self.assertEqual(self.latest_date, latest.date, args)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)


class TestParseLogFile(unittest.TestCase):
    def setUp(self):
        self.sample = r'(?P<url>\S+) (?P<request_time>\d+\.\d+)'
        self.temp_dir = tempfile.mkdtemp()
        self.data = (
            ('/api/v2/banner/25019354', '0.390'),
            ('/api/1/photogenic_banners/list/?server_name=WIN7RB4', '0.133'),
            ('/api/v2/banner/16852664', '0.199'),
            ('/api/v2/slot/4705/groups', '0.704')
        )

        self.plain_temp_file = os.path.join(self.temp_dir, 'log')
        with open(self.plain_temp_file, 'w') as tf:
            tf.writelines([' '.join(words) for words in self.data])

        self.gzip_temp_file = os.path.join(self.temp_dir, 'log.gz')
        with gzip.open(self.gzip_temp_file, 'w') as tf:
            tf.writelines([' '.join(words) for words in self.data])

    def test_parse_if_log_plain(self):
        for parsed in log_analyzer.parse_log(self.plain_temp_file, re.compile(self.sample), compressed=False):
            self.assertTrue(parsed in self.data, (self.sample, self.data))

    def test_parse_if_log_gzip(self):
        for parsed in log_analyzer.parse_log(self.gzip_temp_file, re.compile(self.sample), compressed=True):
            self.assertTrue(parsed in self.data, (self.sample, self.data))

    def tearDown(self):
        shutil.rmtree(self.temp_dir)


class TestSQLite(unittest.TestCase):
    def setUp(self):
        self.conn = log_analyzer.init_db()
        self.curs = self.conn.cursor()

    def test_tables_list(self):
        self.curs.execute("SELECT name FROM sqlite_master WHERE type='table'")
        self.assertEqual(self.curs.fetchall(), [('requests',)])

    def test_text_factory_return_bytestrings(self):
        url, duration = '/api/1/photogenic_banners/list', 0.1
        self.curs.execute("INSERT INTO requests(url, request_time) VALUES (?, ?)", (url, duration))
        self.curs.execute("SELECT url FROM requests")
        self.assertIsInstance(self.curs.fetchone()[0], str)

    def test_fill_requests_table(self):
        url, count = '/api/v2/banner/16852662', 100
        data = [(url, t / 10.0) for t in xrange(0, count, 1)]
        log_analyzer.fill_table(self.conn, data)
        self.curs.execute("SELECT url, request_time FROM requests WHERE url IS ?", (url, ))
        self.assertEqual(data, self.curs.fetchall())

    def test_get_requests_count(self):
        url, count = '/api/v2/banner/16852663', 100
        data = [(url, t / 10.0) for t in xrange(0, count, 1)]
        self.curs.execute("DROP TABLE requests")
        self.curs.execute("CREATE TABLE requests (url TEXT, request_time REAL)")
        self.conn.executemany("INSERT INTO requests(url, request_time) VALUES (?, ?)", data)
        self.assertEqual(count, log_analyzer.get_requests_count(self.conn))

    def test_get_errors_count(self):
        url, count = None, 100
        data = [(url, t / 10.0) for t in xrange(0, count, 1)]
        self.curs.execute("DROP TABLE requests")
        self.curs.execute("CREATE TABLE requests (url TEXT, request_time REAL)")
        self.conn.executemany("INSERT INTO requests(url, request_time) VALUES (?, ?)", data)
        self.assertEqual(count, log_analyzer.get_errors_count(self.conn))

    def test_get_total_time_sum(self):
        data = [('/api/v2/banner/{}'.format(t), t / 10.0) for t in xrange(0, 100, 1)]
        total_time = sum(map(lambda x: x[1], data))
        self.curs.execute("DROP TABLE requests")
        self.curs.execute("CREATE TABLE requests (url TEXT, request_time REAL)")
        self.conn.executemany("INSERT INTO requests(url, request_time) VALUES (?, ?)", data)
        self.assertEqual(total_time, log_analyzer.get_total_time(self.conn))

    def test_median_if_odd_row(self):
        url = '/api/v2/banner/16852664'
        data = [(url, t / 10.0) for t in xrange(0, 99, 1)]
        self.conn.executemany("INSERT INTO requests(url, request_time) VALUES (?, ?)", data)
        self.curs.execute("SELECT MEDIAN(request_time) FROM requests WHERE url IS ?", (url, ))
        self.assertEqual(4.9, self.curs.fetchone()[0])

    def test_median_if_even_row(self):
        url = '/api/v2/banner/16852665'
        data = [(url, t / 10.0) for t in xrange(0, 100, 1)]
        self.conn.executemany("INSERT INTO requests(url, request_time) VALUES (?, ?)", data)
        self.curs.execute("SELECT MEDIAN(request_time) FROM requests WHERE url IS ?", (url, ))
        self.assertEqual(4.95, self.curs.fetchone()[0])

    def test_get_requests_stats_if_no_limit(self):
        d0 = [('/api/v2/banner/16852666', t / 5.0) for t in xrange(0, 100, 1)]
        d1 = [('/api/v2/banner/16852667', t / 10.0) for t in xrange(0, 100, 1)]
        d2 = [('/api/v2/banner/16852668', t / 20.0) for t in xrange(0, 100, 1)]

        expected = [
            ('/api/v2/banner/16852666', 100, 990.0, 9.9, 19.8, 9.9),
            ('/api/v2/banner/16852667', 100, 495.0, 4.95, 9.9, 4.95),
            ('/api/v2/banner/16852668', 100, 247.5, 2.475, 4.95, 2.475)
        ]

        self.curs.execute("DROP TABLE requests")
        self.curs.execute("CREATE TABLE requests (url TEXT, request_time REAL)")
        self.conn.executemany("INSERT INTO requests(url, request_time) VALUES (?, ?)", d0 + d1 + d2)
        requests = [r for r in log_analyzer.get_requests_stats(self.conn, limit=None)]
        self.assertEqual(expected, requests)

    def tearDown(self):
        self.curs.close()
        self.conn.close()


class TestAggrStat(unittest.TestCase):
    def setUp(self):
        d0 = [t / 5.0 for t in xrange(0, 100, 1)]
        d1 = [t / 10.0 for t in xrange(0, 100, 1)]
        d2 = [t / 20.0 for t in xrange(0, 100, 1)]

        self.data = (
            ('/api/v2/banner/166', len(d0), round(sum(d0), 3), round(sum(d0) / len(d0), 3), round(max(d0), 3), 9.9),
            ('/api/v2/banner/167', len(d1), round(sum(d1), 3), round(sum(d1) / len(d1), 3), round(max(d1), 3), 4.95),
            ('/api/v2/banner/168', len(d2), round(sum(d2), 3), round(sum(d2) / len(d2), 3), round(max(d2), 3), 2.475),
        )

        self.total_time = sum(d0) + sum(d1) + sum(d2)
        self.total_count = len(d0) + len(d1) + len(d2)

        self.expected = [
            {'url': '/api/v2/banner/166',
             'count': len(d0),
             'time_sum': round(sum(d0), 3),
             'time_avg': round(sum(d0) / len(d0), 3),
             'time_max': round(max(d0), 3),
             'time_med': 9.9,
             'time_perc': round((sum(d0) * 100.0) / self.total_time, 3),
             'count_perc': round((len(d0) * 100.0) / self.total_count, 3),
             },
            {'url': '/api/v2/banner/167',
             'count': len(d1),
             'time_sum': round(sum(d1), 3),
             'time_avg': round(sum(d1) / len(d1), 3),
             'time_max': round(max(d1), 3),
             'time_med': 4.95,
             'time_perc': round((sum(d1) * 100.0) / self.total_time, 3),
             'count_perc': round((len(d1) * 100.0) / self.total_count, 3),
             },
            {'url': '/api/v2/banner/168',
             'count': len(d2),
             'time_sum': round(sum(d2), 3),
             'time_avg': round(sum(d2) / len(d0), 3),
             'time_max': round(max(d2), 3),
             'time_med': 2.475,
             'time_perc': round((sum(d2) * 100.0) / self.total_time, 3),
             'count_perc': round((len(d2) * 100.0) / self.total_count, 3),
             },
        ]

    def test_aggr_requests_stat(self):
        aggr = log_analyzer.aggr_requests_stat(self.data, self.total_time, self.total_count)
        self.assertEqual(self.expected, aggr)


class TestRenderTemplate(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.src = os.path.join(self.temp_dir, 'report.template.html')
        self.dst = os.path.join(self.temp_dir, 'report.html')

        template = """
        <script type="text/javascript">
            !function($) {
                var table = $table_json;
                var $table = $(".report-table-body");
                var $header = $(".report-table-header-row");
            }
        </script>
        """

        with open(self.src, 'wb') as tf:
            tf.write(template)

        self.data = {
            'table_json': [
                [('a', 1), ('b', 2), ('c', 3), ('d', 4.0)],
                [('e', 5), ('f', 6), ('g', 7), ('h', 8.8)]
            ]
        }

        self.expected = """
        <script type="text/javascript">
            !function($) {
                var table = [[('a', 1), ('b', 2), ('c', 3), ('d', 4.0)], [('e', 5), ('f', 6), ('g', 7), ('h', 8.8)]];
                var $table = $(".report-table-body");
                var $header = $(".report-table-header-row");
            }
        </script>
        """

    def test_render_tamplate(self):
        log_analyzer.render_template(self.src, self.dst, self.data)

        with open(self.dst, 'rb') as tf:
            result = tf.read()

        self.assertEqual(self.expected, result)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)


if __name__ == "__main__":
    unittest.main()
