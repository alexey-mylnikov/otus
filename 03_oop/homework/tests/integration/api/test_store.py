import os
import time
import json
import unittest
import functools
from mock import Mock, DEFAULT
from app.api.store import Store


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


class TestStore(unittest.TestCase):
    def setUp(self):
        self.store = Store(os.getenv('REDIS_HOST'))

    @cases([(12, 2), (42, 3), (15, 4)])
    def test_retry_wrapper_call_func_n_times_if_exception_raises(self, value, retry):
        side_effect = [Exception()] * retry
        side_effect.append(DEFAULT)
        mock_call = Mock()
        mock_call.side_effect = side_effect
        mock_call.return_value = value
        self.store.retry = retry
        my_callable = self.store._retry_wrapper(mock_call)
        self.assertEqual(value, my_callable(), value)

    @cases([12, 4, 15])
    def test_retry_wrapper_call_func_one_time_if_exception_not_raises(self, value):
        mock_call = Mock()
        mock_call.return_value = value
        self.store.retry = 0
        my_callable = self.store._retry_wrapper(mock_call)
        self.assertEqual(value, my_callable(), value)

    @cases([('a', 0), ('b', 1, 10), ('c', -2), ('d', 3.3, 20), ('e', -4.4), ('f', 2 ** 32, 30)])
    def test_set_get_return_value_if_not_expire(self, key, value, expired=None):
        self.store.set(key, json.dumps(value), expired)
        self.assertEqual(value, json.loads(self.store.get(key)), (key, value, expired))

    @cases([('a', 0), ('b', 1, 10), ('c', -2), ('d', 3.3, 20), ('e', -4.4), ('f', 2 ** 32, 30)])
    def test_cache_set_cache_get_return_value_if_not_expire(self, key, value, expired=None):
        self.store.cache_set(key, value, expired)
        self.assertEqual(value, self.store.cache_get(key), (key, value, expired))

    @cases([('a', 0, 1), ('b', 1, 2), ('c', -2, 3), ('d', 3.3, 2), ('e', -4.4, 1)])
    def test_set_get_return_none_if_expire(self, key, value, expired):
        self.store.set(key, json.dumps(value), expired)
        time.sleep(expired + 0.5)
        value = self.store.get(key)
        value = json.loads(key) if value else None
        self.assertEqual(None, value, (key, value, expired))

    @cases([('a', 0, 1), ('b', 1, 2), ('c', -2, 3), ('d', 3.3, 2), ('e', -4.4, 1)])
    def test_cache_set_cache_get_return_none_if_expire(self, key, value, expired):
        self.store.cache_set(key, value, expired)
        time.sleep(expired + 0.5)
        self.assertEqual(None, self.store.cache_get(key), (key, value, expired))


if __name__ == "__main__":
    unittest.main()
