import time
import unittest
from app.api.cache import Cache
from app.api.exceptions import CacheKeyError


class TestCache(unittest.TestCase):
    def setUp(self):
        self.data = (
            ('eb808e52c6cfa4b8765c64c41ee75ff7', 1.5),
            ('e243423b809c4df653c0b665773eaf7f', 2.5),
            ('214435e30fba2160db9df894126206ef', 3.5),
            ('2d22eeb422dfc1fe2eb025c7bcf0a58b', 4.5),
            ('2fe2e370c3d386b78b5aea46114d43a3', 5.5),
            ('3cc214c03400a3535ed740d9d62a32b7', 6.5),
            ('b352783c333c23e62ae136942dbaa49c', 7.5),
            ('0fc78e4fddc4865c1899025673e71bbb', 8.5),
            ('eb808e52c6cfa4b8765c64c41ee75ff7', 9.5),
            ('e243423b809c4df653c0b665773eaf7f', 10.5),
            ('214435e30fba2160db9df894126206ef', 11.5),
            ('2d22eeb422dfc1fe2eb025c7bcf0a58b', 12.5),
            ('2fe2e370c3d386b78b5aea46114d43a3', 13.5),
            ('3cc214c03400a3535ed740d9d62a32b7', 14.5),
            ('b352783c333c23e62ae136942dbaa49c', 15.5),
            ('0fc78e4fddc4865c1899025673e71bbb', 16.5),
        )

    def test_get_value_successful_if_key_exists(self):
        cache = Cache(size=1)
        key, value = self.data[0]

        cache.append(key, value)
        self.assertEqual(cache.get(key), value, value)

    def test_get_value_raises_if_key_not_exists(self):
        cache = Cache(size=1)
        key, __ = self.data[0]

        with self.assertRaises(CacheKeyError):
            cache.get(key)

    def test_set_expireat_successful_if_key_exists(self):
        cache = Cache(size=1)
        key, value = self.data[0]

        cache.append(key, value)
        cache.expireat(key, time.time() + 2)

    def test_set_expireat_raises_if_key_not_exists(self):
        cache = Cache(size=1)
        key, _ = self.data[0]

        with self.assertRaises(CacheKeyError):
            cache.expireat(key, int(time.time()))

    def test_store_all_values_if_keys_unique(self):
        data = tuple({k: v for k, v in self.data}.items())
        cache_size = len(data)
        cache = Cache(size=cache_size)

        for key, value in data:
            cache.append(key, value)
        for key, value in data:
            self.assertEqual(value, cache.get(key), value)

    def test_store_latest_values_if_keys_not_unique(self):
        data = self.data
        expected = tuple({k: v for k, v in data}.items())
        cache_size = len(data)
        cache = Cache(size=cache_size)

        for key, value in data:
            cache.append(key, value)
        for key, value in expected:
            self.assertEqual(value, cache.get(key), value)

    def test_store_latest_values_if_capacity_exhausted(self):
        data = self.data
        cache_size = len(data) / 2
        cache = Cache(size=cache_size)
        expected = tuple({k: v for k, v in data}.items()[:-(cache_size + 1):-1])

        for key, value in data:
            cache.append(key, value)
        for key, value in expected:
            self.assertEqual(value, cache.get(key), value)

    def test_get_value_successful_if_key_not_expired(self):
        cache = Cache(size=1)
        key, value = self.data[0]

        cache.append(key, value)
        cache.expireat(key, time.time() + 10)
        cache.get(key)

    def test_get_value_raises_if_key_expired(self):
        delta = 2
        cache = Cache(size=1)
        key, value = self.data[0]

        cache.append(key, value)
        cache.expireat(key, time.time() + delta)

        time.sleep(delta + 1)
        with self.assertRaises(CacheKeyError):
            cache.get(key)


if __name__ == "__main__":
    unittest.main()
