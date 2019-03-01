import time


class MockRedis(object):
    def __init__(self, *args, **kwargs):
        self.data_table = {}
        self.exp_table = {}

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

    def expireat(self, name, when):
        try:
            self.exp_table[name] = when
        except KeyError:
            return None
