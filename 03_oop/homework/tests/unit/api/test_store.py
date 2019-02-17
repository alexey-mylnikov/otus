import unittest
from app.api.store import Store


def counter(success_on=1):
    i = [0, success_on]

    def incr():
        i[0] = i[0] + 1
        assert i[0] == i[1], 'Fake exception'
        return i[0]

    return incr


class TestStore(unittest.TestCase):
    def test_retry_wrapper_call_func_one_time_if_exception_not_raises(self):
        func = counter()
        wrapped = Store('10', 'localhost')._retry_wrapper(func)
        self.assertEqual(1, wrapped(), 1)

    def test_retry_wrapper_call_func_n_times_if_exception_raises(self):
        retry = 3
        func = counter(success_on=3)
        wrapped = Store('10', 'localhost', retry=retry)._retry_wrapper(func)

        self.assertEqual(retry, wrapped(), retry)

    def test_set_value_success_if_store_available_and_key_unique(self):
        pass

    def test_set_value_success_if_store_available_and_key_not_unique(self):
        pass

    def test_set_value_raises_if_store_unavailable(self):
        pass

    def test_get_value_success_if_store_available_and_key_exists(self):
        pass

    def test_get_value_raises_if_store_available_and_key_not_exists(self):
        pass

    def test_get_value_raises_if_store_unavailable(self):
        pass

    def test_get_value_success_if_store_available_and_key_not_expired(self):
        pass

    def test_get_value_success_if_store_available_and_key_expired(self):
        pass

    def test_set_cache_value_success_if_store_available(self):
        pass

    def test_set_cache_value_success_if_store_unavailable(self):
        pass

    def test_get_cache_value_success_if_store_available(self):
        pass

    def test_get_cache_value_success_if_store_unavailable(self):
        pass


if __name__ == "__main__":
    unittest.main()
