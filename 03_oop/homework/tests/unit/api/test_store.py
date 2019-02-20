import unittest
from mock import patch
from app.api.store import Store
from tests.mixins import AssertMixin
from tests.mocks import MockRedis
from tests.decorators import cases

E = Exception


class TestStore(AssertMixin, unittest.TestCase):
    @patch('redis.Redis', **{'return_value.append.side_effect': [None, None, None]})
    @cases([('a', 0, 1), ('b', 1, 2), ('c', -2, 3)])
    def test_retry_wrapper_call_set_one_time_if_exception_not_raises(self, mock_redis, key, value, retry):
        with self.assertNotRaises(E):
            Store('mocked', retry=retry).set(key, value)

    @patch('redis.Redis', **{'return_value.append.side_effect': [E(), None, E(), E(), None, E(), E(), E(), None]})
    @cases([('a', 0, 1), ('b', 1, 2), ('c', -2, 3)])
    def test_retry_wrapper_call_set_n_times_if_exception_raises(self, mock_redis, key, value, retry):
        with self.assertNotRaises(E):
            Store('mocked', retry=retry).set(key, value)

    @patch('redis.Redis', **{'return_value.get.side_effect': [None, None, None]})
    @cases([('a', 1), ('b', 2), ('c', 3)])
    def test_retry_wrapper_call_get_one_time_if_exception_not_raises(self, mock_redis, key, retry):
        with self.assertNotRaises(E):
            Store('mocked', retry=retry).get(key)

    @patch('redis.Redis', **{'return_value.get.side_effect': [E(), None, E(), E(), None, E(), E(), E(), None]})
    @cases([('a', 0, 1), ('b', 1, 2), ('c', -2, 3)])
    def test_retry_wrapper_call_get_n_times_if_exception_raises(self, mock_redis, key, value, retry):
        with self.assertNotRaises(E):
            Store('mocked', retry=retry).set(key, value)

    @patch('redis.Redis', **{'return_value': MockRedis()})
    @cases([('a', 0), ('b', 1, 10), ('c', -2), ('d', 3.3, 20), ('e', -4.4), ('f', 2 ** 32, 30)])
    def test_set_success_if_store_available(self, mock_redis, key, value, expired=None):
        with self.assertNotRaises(E):
            Store('mocked').set(key, value, expired)

    @patch('redis.Redis', **{'return_value.append.side_effect': E()})
    @cases([('a', 0), ('b', 1, 10), ('c', -2), ('d', 3.3, 20), ('e', -4.4), ('f', 2 ** 32, 30)])
    def test_set_raises_if_store_unavailable(self, mock_redis, key, value, expired=None):
        with self.assertRaises(E):
            Store('mocked').set(key, value, expired)

    @patch('redis.Redis', **{'return_value': MockRedis()})
    @cases(['a', 'b', 'c', 'd', 'e', 'f'])
    def test_get_success_if_store_available(self, mock_redis, key):
        with self.assertNotRaises(E):
            Store('mocked').get(key)

    @patch('redis.Redis', **{'return_value.get.side_effect': E()})
    @cases(['a', 'b', 'c', 'd', 'e', 'f'])
    def test_get_raises_if_store_unavailable(self, mock_redis, key):
        with self.assertRaises(E):
            Store('mocked').get(key)

    @patch('redis.Redis', **{'return_value': MockRedis()})
    @cases([('a', 0), ('b', 1, 10), ('c', -2), ('d', 3.3, 20), ('e', -4.4), ('f', 2 ** 32, 30)])
    def test_cache_set_success_if_store_available(self, mock_redis, key, value, expired=None):
        with self.assertNotRaises(E):
            Store('mocked').cache_set(key, value, expired)

    @patch('redis.Redis', **{'return_value.append.side_effect': E()})
    @cases([('a', 0), ('b', 1, 10), ('c', -2), ('d', 3.3, 20), ('e', -4.4), ('f', 2 ** 32, 30)])
    def test_cache_set_success_if_store_unavailable(self, mock_redis, key, value, expired=None):
        with self.assertNotRaises(E):
            Store('mocked').cache_set(key, value, expired)

    @patch('redis.Redis', **{'return_value': MockRedis()})
    @cases(['a', 'b', 'c', 'd', 'e', 'f'])
    def test_cache_get_success_if_store_available(self, mock_redis, key):
        with self.assertNotRaises(E):
            Store('mocked').cache_get(key)

    @patch('redis.Redis', **{'return_value.append.side_effect': E()})
    @cases(['a', 'b', 'c', 'd', 'e', 'f'])
    def test_cache_get_success_if_store_unavailable(self, mock_redis, key):
        with self.assertNotRaises(E):
            Store('mocked').cache_get(key)


if __name__ == "__main__":
    unittest.main()
