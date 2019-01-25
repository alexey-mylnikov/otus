# -*- coding: utf-8 -*-
from base import BaseField, BaseForm


class CharField(BaseField):
    def __init__(self, required=False, nullable=True):
        super(CharField, self).__init__(type=(str, unicode), required=required, nullable=nullable)


class ArgumentsField(BaseField):
    def __init__(self, required=False, nullable=True):
        super(ArgumentsField, self).__init__(type=BaseForm, required=required, nullable=nullable)


class EmailField(CharField):
    def __init__(self, required=False, nullable=True):
        super(EmailField, self).__init__(required=required, nullable=nullable)


class PhoneField(BaseField):
    def __init__(self, required=False, nullable=True):
        super(PhoneField, self).__init__(type=int, required=required, nullable=nullable)


class DateField(BaseField):
    def __init__(self, required=False, nullable=True):
        super(DateField, self).__init__(type=(str, unicode), required=required, nullable=nullable)


class BirthDayField(DateField):
    def __init__(self, required=False, nullable=True):
        super(BirthDayField, self).__init__(required=required, nullable=nullable)


class GenderField(BaseField):
    def __init__(self, required=False, nullable=True):
        super(GenderField, self).__init__(type=(str, unicode), required=required, nullable=nullable)


class ClientIDsField(BaseField):
    def __init__(self, required=False, nullable=True):
        super(ClientIDsField, self).__init__(type=(str, unicode), required=required, nullable=nullable)
