import os
import json
import redis
import random
import hashlib
import httplib
import datetime
import unittest
import functools
from app.api import consts


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


class AppTest(unittest.TestCase):
    host, port = '0.0.0.0', 8080

    def setUp(self):
        store = redis.Redis(os.getenv('REDIS_HOST'))
        interests = ("cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus")
        for key in (0, 1, 2, 3):
            store.set("i:{}".format(key), json.dumps(random.sample(interests, 2)))

        self.conn = httplib.HTTPConnection(self.host, self.port, timeout=10)

    @staticmethod
    def set_valid_auth(request):
        if request.get("login") == consts.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + consts.ADMIN_SALT).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + consts.SALT
            request["token"] = hashlib.sha512(msg).hexdigest()

    def get_response(self, request):
        self.conn.request('POST', '/method', body=json.dumps(request))
        resp = json.loads(self.conn.getresponse().read())
        return resp.get('response'), resp.get('code')

    def test_success_score_admin_request(self):
        arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
        request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        resp, code = self.get_response(request)
        score = resp.get('score')
        self.assertEqual(consts.OK, code, arguments)
        self.assertEqual(score, 42)

    @cases([
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_success_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        resp, code = self.get_response(request)
        score = resp.get('score')
        self.assertEqual(consts.OK, code, arguments)
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_ok_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        resp, code = self.get_response(request)
        self.assertEqual(consts.OK, code, arguments)
        self.assertEqual(len(arguments["client_ids"]), len(resp))
        self.assertTrue(all(v and isinstance(v, list) and all(isinstance(i, basestring) for i in v)
                            for v in resp.values()))

    def tearDown(self):
        self.conn.close()
