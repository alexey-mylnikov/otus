import unittest
from contextlib import contextmanager


class AssertMixin(unittest.TestCase):
    @contextmanager
    def assertNotRaises(self, exception):
        try:
            yield None
        except exception:
            raise self.failureException('raised')
