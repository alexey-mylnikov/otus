import unittest
from unit.mixins import AssertMixin
from unit.decorators import cases
from app.api.consts import GENDERS
from app.api.exceptions import ValidationError
from app.api.fields import (
    CharField, ArgumentsField,
    EmailField, PhoneField,
    DateField, BirthDayField,
    GenderField, ClientIDsField
)


class FieldsMixin(AssertMixin, unittest.TestCase):
    @staticmethod
    def requestFabric(name, cls, **kwargs):
        return type('Request', (object,), {name: cls(**kwargs), '__init__': lambda self, v: setattr(self, name, v)})

    def assertValid(self, field, value, **kwargs):
        cls = self.requestFabric(field.__name__, field, **kwargs)
        with self.assertNotRaises(ValidationError):
            cls(value)

    def assertInvalid(self, field, value, **kwargs):
        cls = self.requestFabric(field.__name__, field, **kwargs)
        with self.assertRaises(ValidationError):
            cls(value)


class TestCharField(FieldsMixin, unittest.TestCase):
    @cases(['', 'a', 'abc', u'def'])
    def test_init_success_if_nullable_and_valid_value(self, value):
        self.assertValid(CharField, value, nullable=True)

    @cases([''])
    def test_init_raises_if_not_nullable_and_valid_null_value(self, value):
        self.assertInvalid(CharField, value, nullable=False)

    @cases([None, True, False, 0, 1, 1.2, [1, 2], {'a': 1, 'b': 2}])
    def test_init_raises_if_invalid_value(self, value):
        self.assertInvalid(CharField, value)


class TestArgumentsField(FieldsMixin, unittest.TestCase):
    @cases([{}, {'a': 1, 'b': 2}])
    def test_init_success_if_nullable_and_valid_value(self, value):
        self.assertValid(ArgumentsField, value, nullable=True)

    @cases([{}])
    def test_init_raises_if_not_nullable_and_valid_null_value(self, value):
        self.assertInvalid(ArgumentsField, value, nullable=False)

    @cases([None, True, False, 0, 1.2, [1, 2], '3 4'])
    def test_init_raises_if_invalid_value(self, value):
        self.assertInvalid(ArgumentsField, value)


class TestEmailField(FieldsMixin, unittest.TestCase):
    @cases(['', 'valid@email', u'valid@email'])
    def test_init_success_if_nullable_and_valid_value(self, value):
        self.assertValid(EmailField, value, nullable=True)

    @cases([''])
    def test_init_raises_if_not_nullable_and_valid_null_value(self, value):
        self.assertInvalid(EmailField, value, nullable=False)

    @cases(['invalid_email', u'invalid_email'])
    def test_init_raises_if_invalid_value(self, value):
        self.assertInvalid(EmailField, value)


class TestPhoneField(FieldsMixin, unittest.TestCase):
    @cases(['', 79998887766, '79998887766', u'79998887766'])
    def test_init_success_if_nullable_and_valid_value(self, value):
        self.assertValid(PhoneField, value, nullable=True)

    @cases([None, ''])
    def test_init_raises_if_not_nullable_and_valid_null_value(self, value):
        self.assertInvalid(PhoneField, value, nullable=False)

    @cases([0, 1.2, -3, '89998887766', 89998887766, '9998887766', 9998887766])
    def test_init_raises_if_invalid_value(self, value):
        self.assertInvalid(PhoneField, value)


class TestDateField(FieldsMixin, unittest.TestCase):
    @cases(['', '01.01.1001', '20.02.2019', '20.02.2039'])
    def test_init_success_if_nullable_and_valid_value(self, value):
        self.assertValid(DateField, value, nullable=True)

    @cases([''])
    def test_init_raises_if_not_nullable_and_valid_null_value(self, value):
        self.assertInvalid(DateField, value, nullable=False)

    @cases([20022019, 200219, '20.02.19', '20-02-2019', 20190220, 190220, '2019.02.20', '2019-02-20'])
    def test_init_raises_if_invalid_value(self, value):
        self.assertInvalid(DateField, value)


class TestBirthdayField(FieldsMixin, unittest.TestCase):
    @cases(['', '20.02.2010'])
    def test_init_success_if_nullable_and_valid_value(self, value):
        self.assertValid(BirthDayField, value, nullable=True)

    @cases([''])
    def test_init_raises_if_not_nullable_and_valid_null_value(self, value):
        self.assertInvalid(BirthDayField, value, nullable=False)

    @cases(['20.02.1001'])
    def test_init_raises_if_invalid_value(self, value):
        self.assertInvalid(BirthDayField, value)


class TestGenderField(FieldsMixin, unittest.TestCase):
    @cases(GENDERS.keys())
    def test_init_success_if_nullable_and_valid_value(self, value):
        self.assertValid(GenderField, value, nullable=True)

    @cases([-1, 1.1, 42, '0', '1', '2'])
    def test_init_raises_if_invalid_value(self, value):
        self.assertInvalid(GenderField, value)


class TestClientIdsField(FieldsMixin, unittest.TestCase):
    @cases([[], [0], [1, 2, 3, 4]])
    def test_init_success_if_nullable_and_valid_value(self, value):
        self.assertValid(ClientIDsField, value, nullable=True)

    @cases([[]])
    def test_init_raises_if_not_nullable_and_valid_null_value(self, value):
        self.assertInvalid(ClientIDsField, value, nullable=False)

    @cases([[1, 2, -3], ['1', 2, 3], [1.2, 3, 4.5]])
    def test_init_raises_if_invalid_value(self, value):
        self.assertInvalid(ClientIDsField, value)


if __name__ == "__main__":
    unittest.main()
