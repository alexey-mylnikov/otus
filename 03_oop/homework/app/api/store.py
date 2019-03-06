import time
import json
import redis


class Store(object):
    def __init__(self, host, timeout=5, retry=3, backoff=0.3, **kwargs):
        kwargs['socket_timeout'] = timeout
        self.store = redis.Redis(host,  **kwargs)
        self.retry = retry
        self.backoff = backoff

    def _retry_wrapper(self, func):
        def wrapper(*args, **kwargs):
            tries = self.retry or 0

            while tries > 0:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    time.sleep(self.backoff * (2 ** (self.retry - tries)))
                    tries -= 1

            return func(*args, **kwargs)
        return wrapper

    def set(self, key, value, expire=None):
        self._retry_wrapper(self.store.set)(key, value, ex=expire)

    def get(self, key):
        return self._retry_wrapper(self.store.get)(key)

    def cache_set(self, key, value, expire=None, prefix='cache'):
        key = '{}_{}'.format(prefix, key)

        try:
            self.store.set(key, json.dumps(value), ex=expire)
        except Exception:
            pass

    def cache_get(self, key, prefix='cache'):
        key = '{}_{}'.format(prefix, key)

        try:
            return json.loads(self.store.get(key))
        except Exception:
            return None
