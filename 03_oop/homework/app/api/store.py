import time
import redis


class Cache(object):
    def __init__(self):
        self.data_table = {}
        self.exp_table = {}

    def expireat(self, name, when):
        try:
            self.exp_table[name] = when
        except KeyError:
            return None

    def append(self, key, value):
        try:
            del self.data_table[key]
            del self.exp_table[key]
        except KeyError:
            pass

        self.data_table[key] = value

    def get(self, name):
        try:
            value = self.data_table[name]
        except KeyError:
            return None

        expire = self.exp_table.get(name)

        if expire is not None and expire < int(time.time()):
            __ = self.data_table.pop(name, None)
            __ = self.exp_table.pop(name, None)
            return None

        return value


class Store(object):
    def __init__(self, host, timeout=5, retry=3, backoff=0.3, **kwargs):
        kwargs['socket_timeout'] = timeout
        self.store = redis.Redis(host,  **kwargs)
        self.retry = retry
        self.backoff = backoff
        self.cache = Cache()

    def _retry_wrapper(self, func):
        def wrapper(*args, **kwargs):
            tries = self.retry or 1

            while tries > 0:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    time.sleep(self.backoff * (2 ** (self.retry - tries)))
                    tries -= 1

            return func(*args, **kwargs)
        return wrapper

    def set(self, key, value, expire=None):
        self._retry_wrapper(self.store.append)(key, value)
        if expire:
            self._retry_wrapper(self.store.expireat)(key, int(time.time() + expire))

    def get(self, key):
            return self._retry_wrapper(self.store.get)(key)

    def cache_set(self, key, value, expire=None):
        self.cache.append(key, value)
        if expire:
            self.cache.expireat(key, int(time.time() + expire))

    def cache_get(self, key):
        return self.cache.get(key)
