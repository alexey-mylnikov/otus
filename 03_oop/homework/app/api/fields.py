# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime
from base import BaseField
from exceptions import ValidationError
from consts import GENDERS, UNKNOWN, DATE_FORMAT


class CharField(BaseField):
    def __init__(self, required=False, nullable=True):
        super(CharField, self).__init__(type=(str, unicode), required=required, nullable=nullable)


class ArgumentsField(BaseField):
    def __init__(self, required=False, nullable=True):
        super(ArgumentsField, self).__init__(type=dict, required=required, nullable=nullable)


class EmailField(CharField):
    def __init__(self, required=False, nullable=True):
        super(EmailField, self).__init__(required=required, nullable=nullable)

    def validate(self, value):
        super(EmailField, self).validate(value)

        if value and '@' not in value:
            raise ValidationError('invalid email address "{}"'.format(value))


class PhoneField(BaseField):
    def __init__(self, required=False, nullable=True):
        super(PhoneField, self).__init__(type=(int, str, unicode), required=required, nullable=nullable)

    def validate(self, value):
        super(PhoneField, self).validate(value)

        value = value and str(value)

        if value and (not value.isdigit() or not value.startswith('7') or (len(value) != 11)):
            raise ValidationError('invalid phone number {}'.format(value))


class DateField(BaseField):
    def __init__(self, required=False, nullable=True):
        super(DateField, self).__init__(type=(str, unicode), required=required, nullable=nullable)

    def validate(self, value):
        super(DateField, self).validate(value)

        if value:
            try:
                datetime.strptime(value, DATE_FORMAT)
            except ValueError:
                raise ValidationError('invalid date format')


class BirthDayField(DateField):
    def __init__(self, required=False, nullable=True):
        super(BirthDayField, self).__init__(required=required, nullable=nullable)

    def validate(self, value):
        super(BirthDayField, self).validate(value)

        if value:
            try:
                value = datetime.strptime(value, DATE_FORMAT).date()
            except ValueError:
                raise ValidationError('invalid date format')

            if (value + relativedelta(years=70)) < datetime.now().date():
                raise ValidationError('too old')


class GenderField(BaseField):
    def __init__(self, required=False, nullable=True):
        super(GenderField, self).__init__(type=int, required=required, nullable=nullable)

    def validate(self, value):
        if not isinstance(value, self.type):
            raise ValidationError('invalid value type of field "gender"')

        if not value and value != UNKNOWN and not self.nullable:
            ValidationError('field "gender" cannot be empty')

        if value not in GENDERS:
            raise ValidationError('invalid value of field "gender"')


class ClientIDsField(BaseField):
    def __init__(self, required=False, nullable=True):
        super(ClientIDsField, self).__init__(type=(list, tuple), required=required, nullable=nullable)

    def validate(self, value):
        super(ClientIDsField, self).validate(value)

        if value:
            for obj in value:
                if not isinstance(obj, int):
                    raise ValidationError('invalid client id "{}"')
