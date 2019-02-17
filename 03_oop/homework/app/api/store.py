import time
import redis
from app.api.cache import Cache
from app.api.exceptions import CacheKeyError


class Store(object):
    def __init__(self, cache_size, host, timeout=1, retry=3, backoff=0.3, **kwargs):
        self.cache = Cache(cache_size)

        kwargs['socket_timeout'] = timeout
        self.store = redis.Redis(host,  **kwargs)
        self.retry = retry
        self.backoff = backoff

    def _retry_wrapper(self, func):
        def wrapper(*args, **kwargs):
            tries = self.retry or 1

            while tries > 0:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    tries -= 1
                    time.sleep(self.backoff * (2 ** (tries - 1)))

            return func(*args, **kwargs)
        return wrapper

    def set(self, key, value, expire=None):
        when = expire and int(time.time() + expire)

        self.cache.append(key, value)
        self._retry_wrapper(self.store.append)(key, value)

        if when:
            self.cache.expireat(key, when)
            self._retry_wrapper(self.store.expireat)(key, when)

    def get(self, key):
        try:
            return self.cache.get(key)
        except CacheKeyError:
            return self._retry_wrapper(self.store.get)(key)

    def cache_set(self, key, value, expire=None):
        try:
            self.set(key, value, expire)
        except Exception:
            pass

    def cache_get(self, key):
        try:
            return self.get(key)
        except Exception:
            return None
