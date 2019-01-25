# -*- coding: utf-8 -*-
from weakref import WeakKeyDictionary


class BaseField(object):
    name = None

    def __init__(self, type, required=False, nullable=True):
        self.type = type
        self.required = required
        self.nullable = nullable

    def __set__(self, instance, value):
        if not isinstance(value, self.type):
            raise TypeError

        if not (value or self.nullable):
            raise ValueError

        instance.__dict__[self.name] = value

    def __get__(self, instance, owner):
        value = instance.__dict__.get(self.name, None)

        if not value and self.required:
            raise NotImplementedError

        return value


class FormMeta(type):
    def __new__(mcs, name, bases, attrs):
        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, BaseField):
                attr_value.name = attr_name

        return super(FormMeta, mcs).__new__(mcs, name, bases, attrs)


class BaseForm(object):
    __metaclass__ = FormMeta
