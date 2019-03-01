from contextlib import contextmanager


class AssertMixin(object):
    def failureException(self, *args, **kwargs):
        raise NotImplementedError

    @contextmanager
    def assertNotRaises(self, exception):
        try:
            yield None
        except exception:
            raise self.failureException('raised')
