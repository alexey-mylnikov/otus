import time
import redis


class Store(object):
    def __init__(self, host, timeout=5, retry=3, backoff=0.3, **kwargs):
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
        self._retry_wrapper(self.store.append)(key, value)
        if expire:
            self._retry_wrapper(self.store.expireat)(key, int(time.time() + expire))

    def get(self, key):
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
