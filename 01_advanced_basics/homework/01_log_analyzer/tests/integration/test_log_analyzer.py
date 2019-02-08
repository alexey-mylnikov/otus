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

        with open(os.path.join(reports, 'golden.report-2017.07.01.html'), 'rb') as gr:
            self.golden = gr.read()

        with open(log_analyzer.main(**config), 'rb') as r:
            self.report = r.read()

    def test_log_analyzer_report(self):
        self.assertMultiLineEqual(self.golden, self.report)


if __name__ == "__main__":
    unittest.main()
