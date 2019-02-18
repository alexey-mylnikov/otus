#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import unittest
from log_analyzer import log_analyzer


class TestLogAnalyzer(unittest.TestCase):
    def setUp(self):
        fixtures = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fixtures')
        reports = os.path.join(fixtures, 'reports')
        logs = os.path.join(fixtures, 'log')

        config = {
            "REPORT_DIR": reports,
            "LOG_DIR": logs,
            "ERROR_THRESHOLD": 99
        }

        expected_file = os.path.join(reports, 'report-2017.07.01.html.expected')
        self.report_file = log_analyzer.main(**config)

        with open(expected_file, 'rb') as gr:
            self.expected = gr.read()

        with open(self.report_file, 'rb') as r:
            self.report = r.read()

    def test_log_analyzer_report(self):
        self.assertMultiLineEqual(self.expected, self.report)

    def tearDown(self):
        os.remove(self.report_file)


if __name__ == "__main__":
    unittest.main()
