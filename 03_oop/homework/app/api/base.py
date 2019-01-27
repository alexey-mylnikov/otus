# -*- coding: utf-8 -*-
from copy import deepcopy


class BaseField(object):
    name = None

    def __init__(self, type, required=False, nullable=True, default=None):
        self.type = type
        self.required = required
        self.nullable = nullable
        self.default = default

    def __set__(self, instance, value):
        self.validate(value)
        instance.__dict__[self.name] = value

    def __get__(self, instance, owner):
        return instance.__dict__.get(self.name, self.default)

    def validate(self, value):
        if not (value or self.nullable):
            raise ValueError('field "{}" cannot be empty'.format(self.name))

        if not isinstance(value, self.type):
            raise TypeError('field "{}", invalid type "{}"'.format(self.name, self.type))


class RequestMeta(type):
    def __new__(mcs, name, bases, attrs):
        _required_fields = []

        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, BaseField):
                attr_value.name = attr_name

                if attr_value.required:
                    _required_fields.append(attr_name)

        cls = super(RequestMeta, mcs).__new__(mcs, name, bases, attrs)
        cls._required_fields = _required_fields

        return cls


class BaseRequest(object):
    __metaclass__ = RequestMeta

    def __init__(self, body):
        body = deepcopy(body)
        self._initialized_fields = []

        for field_name, field_value in body.items():
            setattr(self, field_name, field_value)
            self._initialized_fields.append(field_name)

        missed = set(self._required_fields) - set(self._initialized_fields)
        if missed:
            raise ValueError('missing required fields: "{}"'.format(', '.join(missed)))

    @property
    def initialized_fields(self):
        return self._initialized_fields
