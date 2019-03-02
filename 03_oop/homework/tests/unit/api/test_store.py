import time
import unittest
import functools
from mock import patch
from app.api.store import Cache, Store

E = Exception


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


class TestCache(unittest.TestCase):
    @cases([('a', 2 ** 32, 1), ('b', 'test', 2)])
    def test_get_value_if_not_expired(self, key, value, expired):
        cache = Cache()
        cache.append(key, value)
        cache.expireat(key, int(time.time() + expired))
        self.assertEqual(value, cache.get(key), (key, value))

    @cases([('a', 2 ** 32, 1), ('b', 'test', 2)])
    def test_get_none_if_expired(self, key, value, expired):
        cache = Cache()
        cache.append(key, value)
        cache.expireat(key, int(time.time() + expired))
        time.sleep(expired + 1)
        self.assertEqual(None, cache.get(key), (key, value))


class TestStore(unittest.TestCase):
    @patch('redis.Redis')
    @cases([('a', 0, 1), ('b', 1, 2), ('c', -2, 3)])
    def test_retry_wrapper_call_set_n_times_if_exception_raises(self, mock_redis, key, value, retry):
        side_effect = [E()] * retry
        side_effect.append(None)
        mock_redis.return_value.append.side_effect = side_effect
        mock_redis.return_value.get.return_value = value
        store = Store('mocked', retry=retry)
        store.set(key, value)
        self.assertEqual(value, store.get(key), (key, value))

    @patch('redis.Redis', **{'return_value.get.side_effect': [E(), None, E(), E(), None, E(), E(), E(), None]})
    @cases([('a', 0, 1), ('b', 1, 2), ('c', -2, 3)])
    def test_retry_wrapper_call_get_n_times_if_exception_raises(self, mock_redis, key, value, retry):
        side_effect = [E()] * retry
        side_effect.append(value)
        mock_redis.return_value.append.return_value = None
        mock_redis.return_value.get.side_effect = side_effect
        store = Store('mocked', retry=retry)
        store.set(key, value)
        self.assertEqual(value, store.get(key), (key, value))

    @patch('redis.Redis')
    @cases([('a', 0), ('b', 1, 10), ('c', -2), ('d', 3.3, 20), ('e', -4.4), ('f', 2 ** 32, 30)])
    def test_set_success_if_store_available(self, mock_redis, key, value, expired=None):
        mock_redis.return_value.set.return_value = None
        mock_redis.return_value.get.return_value = value
        store = Store('mocked')
        store.set(key, value, expired)
        self.assertEqual(value, store.get(key), (key, value, expired))

    @patch('redis.Redis')
    @cases([('a', 0), ('b', 1, 10), ('c', -2), ('d', 3.3, 20), ('e', -4.4), ('f', 2 ** 32, 30)])
    def test_get_success_if_store_available(self, mock_redis, key, value, expired=None):
        mock_redis.return_value.set.return_value = None
        mock_redis.return_value.get.return_value = value
        store = Store('mocked')
        store.set(key, value, expired)
        self.assertEqual(value, store.get(key), (key, value, expired))

    @patch('redis.Redis')
    @cases([('a', 0), ('b', 1, 10), ('c', -2), ('d', 3.3, 20), ('e', -4.4), ('f', 2 ** 32, 30)])
    def test_cache_set_success_if_store_available(self, mock_redis, key, value, expired=None):
        mock_redis.return_value.set.return_value = None
        mock_redis.return_value.get.return_value = value
        store = Store('mocked')
        store.cache_set(key, value, expired)
        self.assertEqual(value, store.cache_get(key), (key, value, expired))

    @patch('redis.Redis', **{'return_value.set.side_effect': E(), 'return_value.get.side_effect': E()})
    @cases([('a', 0), ('b', 1, 10), ('c', -2), ('d', 3.3, 20), ('e', -4.4), ('f', 2 ** 32, 30)])
    def test_cache_set_success_if_store_unavailable(self, mock_redis, key, value, expired=None):
        store = Store('mocked')
        store.cache_set(key, value, expired)
        self.assertEqual(value, store.cache_get(key), (key, value, expired))

    @patch('redis.Redis')
    @cases([('a', 0), ('b', 1, 10), ('c', -2), ('d', 3.3, 20), ('e', -4.4), ('f', 2 ** 32, 30)])
    def test_cache_get_success_if_store_available(self, mock_redis, key, value, expired=None):
        mock_redis.return_value.set.side_effect = None
        mock_redis.return_value.get.side_effect = value
        store = Store('mocked')
        store.cache_set(key, value, expired)
        self.assertEqual(value, store.cache_get(key), (key, value, expired))

    @patch('redis.Redis', **{'return_value.set.side_effect': E(), 'return_value.get.side_effect': E()})
    @cases([('a', 0), ('b', 1, 10), ('c', -2), ('d', 3.3, 20), ('e', -4.4), ('f', 2 ** 32, 30)])
    def test_cache_get_success_if_store_unavailable(self, mock_redis, key, value, expired=None):
        store = Store('mocked')
        store.cache_set(key, value, expired)
        self.assertEqual(value, store.cache_get(key), (key, value, expired))


if __name__ == "__main__":
    unittest.main()
