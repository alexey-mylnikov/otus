# -*- coding: utf-8 -*-
from base import BaseRequest
from fields import (
    CharField, ArgumentsField,
    EmailField, PhoneField, DateField,
    BirthDayField, GenderField, ClientIDsField
)
from consts import ADMIN_LOGIN


class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True, nullable=False)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(BaseRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def __init__(self, body):
        super(OnlineScoreRequest, self).__init__(body)

        valid = any(((self.first_name is not None and self.last_name is not None),
                     (self.email is not None and self.phone is not None),
                     (self.birthday is not None and self.gender is not None)))

        if not valid:
            self._errors.append('invalid arguments set')


class MethodRequest(BaseRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=True)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN
