import unittest
import requests
from urlparse import urljoin


class TestIP2W(unittest.TestCase):
    base = 'http://127.0.0.1:8080/'

    def setUp(self):
        self.conn = requests.Session()

    def make_url(self, uri):
        return urljoin(self.base, uri)

    def test_request_success_if_ip_valid(self):
        resp = self.conn.get(self.make_url('/ip2w/176.14.221.123')).json()
        self.assertIsInstance(resp, dict)
        self.assertIsNotNone(resp.get('city'))
        self.assertIsNotNone(resp.get('conditions'))
        self.assertIsNotNone(resp.get('temp'))

    def test_request_success_if_ip_bogus(self):
        resp = self.conn.get(self.make_url('/ip2w/127.0.0.1')).json()
        self.assertIsInstance(resp, dict)
        self.assertIsNotNone(resp.get('error'))

    def test_request_failed_if_ip_not_valid(self):
        resp = self.conn.get(self.make_url('/ip2w/176.14.123'))
        self.assertEqual(resp.status_code, 404)

    def tearDown(self):
        self.conn.close()


