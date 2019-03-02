import unittest
import functools
from app.api.consts import ADMIN_LOGIN
from app.api.requests import (
    ClientsInterestsRequest, OnlineScoreRequest,
    MethodRequest
)


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


class TestClientsInterestsRequest(unittest.TestCase):
    @cases([
        {'client_ids': [0, 1, 2, 3]},
        {'client_ids': [0, 1, 2, 3], 'date': '20.02.2019'}
    ])
    def test_request_valid_if_body_valid(self, body):
        request = ClientsInterestsRequest(body)
        self.assertTrue(request.is_valid)
        self.assertGreaterEqual(len(request.initialized_fields), len(request.required_fields))

    @cases([
        {},
        {'client_ids': []},
        {'client_ids': [-1, 0, 1, 2]}
    ])
    def test_request_invalid_if_body_invalid(self, body):
        self.assertFalse(ClientsInterestsRequest(body).is_valid)


class TestOnlineScoreRequest(unittest.TestCase):
    @cases([
        {'first_name': 'a', 'last_name': 'b'},
        {'email': 'valid@email', 'phone': '79175002040'},
        {'birthday': '20.02.2019', 'gender': 1},
        {'first_name': 'a', 'last_name': 'b', 'email': 'valid@email', 'phone': 79175002040},
        {'first_name': 'a', 'last_name': 'b', 'email': 'valid@email', 'phone': 79175002040,
         'birthday': '20.02.2019', 'gender': 1},
    ])
    def test_request_valid_if_body_valid(self, body):
        request = OnlineScoreRequest(body)
        self.assertTrue(request.is_valid)
        self.assertGreaterEqual(len(request.initialized_fields), len(request.required_fields))

    @cases([
        {},
        {'first_name': 'a', 'email': 'valid@email'},
        {'email': 'valid@email', 'birthday': '20.02.2019'},
        {'birthday': '20.02.2019', 'last_name': 'b'},
    ])
    def test_request_invalid_if_body_invalid(self, body):
        self.assertFalse(OnlineScoreRequest(body).is_valid)


class TestMethodRequest(unittest.TestCase):
    @cases([
        {'login': '', 'token': '', 'arguments': {}, 'method': ''},
        {'login': 'h&f', 'token': '12345', 'arguments': {}, 'method': 'score'},
        {'account': 'horns&hoofs', 'login': 'h&f', 'token': '12345', 'arguments': {'a': 1, 'b': 2}, 'method': 'score'},
    ])
    def test_request_valid_if_body_valid(self, body):
        request = MethodRequest(body)
        self.assertTrue(request.is_valid)
        self.assertGreaterEqual(len(request.initialized_fields), len(request.required_fields))

    @cases([
        {},
        {'token': '12345'},
        {'token': '12345', 'arguments': {}, 'method': 'score'},
    ])
    def test_request_invalid_if_body_invalid(self, body):
        self.assertFalse(MethodRequest(body).is_valid)

    @cases([
        {'login': ADMIN_LOGIN, 'token': '', 'arguments': {}, 'method': ''},
    ])
    def test_admin_login(self, body):
        self.assertTrue(MethodRequest(body).is_admin)


if __name__ == "__main__":
    unittest.main()
