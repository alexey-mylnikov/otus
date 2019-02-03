# -*- coding: utf-8 -*-
from abc import ABCMeta
from copy import deepcopy
from exceptions import ValidationError


class BaseField(object):
    __metaclass__ = ABCMeta

    def __init__(self, type, required=False, nullable=True, default=None):
        self.name = None
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
            raise ValidationError('field "{}" cannot be empty'.format(self.name))

        if not isinstance(value, self.type):
            raise ValidationError('field "{}", invalid type "{}"'.format(self.name, self.type))


class RequestMeta(type):
    def __new__(mcs, name, bases, attrs):
        declared_fields = []
        required_fields = []

        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, BaseField):
                attr_value.name = attr_name

                declared_fields.append(attr_name)

                if attr_value.required:
                    required_fields.append(attr_name)

        cls = super(RequestMeta, mcs).__new__(mcs, name, bases, attrs)

        cls._declared_fields = declared_fields
        cls._required_fields = required_fields

        return cls


class BaseRequest(object):
    __metaclass__ = RequestMeta

    def __init__(self, body):
        self._errors = []
        self._initialized_fields = []

        body = deepcopy(body)

        for field_name, field_value in body.items():
            if field_name not in self._declared_fields:
                self._errors.append('undeclared field "{}"'.format(field_name))
                continue

            try:
                setattr(self, field_name, field_value)
            except ValidationError as e:
                self._errors.append(str(e))
                continue

            self._initialized_fields.append(field_name)

        missed = set(self._required_fields) - set(self._initialized_fields)
        if missed:
            self._errors.append('missing required fields: "{}"'.format(', '.join(missed)))

    @property
    def errors(self):
        return ', '.join(self._errors)

    @property
    def declared_fields(self):
        return self._declared_fields

    @property
    def required_fields(self):
        return self._required_fields

    @property
    def initialized_fields(self):
        return self._initialized_fields

    @property
    def is_valid(self):
        return len(self._errors) == 0
