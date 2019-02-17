# -*- coding: utf-8 -*-
import time
from collections import OrderedDict
from app.api.exceptions import CacheKeyError


class Cache(object):
    def __init__(self, size=None):
        self.size = size
        self.data_table = OrderedDict()
        self.exp_table = OrderedDict()

    def __len__(self):
        return len(self.data_table)

    def append(self, key, value):
        try:
            del self.data_table[key]
            del self.exp_table[key]
        except KeyError:
            pass

        if len(self.data_table) == self.size:
            item, __ = self.data_table.popitem()
            __ = self.exp_table.pop(item, None)

        self.data_table[key] = value

    def get(self, name):
        try:
            value = self.data_table[name]
        except KeyError:
            raise CacheKeyError

        expire = self.exp_table.get(name)

        if expire is not None and expire < int(time.time()):
            __ = self.data_table.pop(name, None)
            __ = self.exp_table.pop(name, None)
            raise CacheKeyError

        return value

    def expireat(self, name, when):
        try:
            self.data_table[name]
        except KeyError:
            raise CacheKeyError

        self.exp_table[name] = when
