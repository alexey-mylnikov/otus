# -*- coding: utf-8 -*-
from base import BaseForm
from fields import (
    CharField, ArgumentsField,
    EmailField, PhoneField, DateField,
    BirthDayField, GenderField, ClientIDsField
)


class ClientsInterestsRequest(BaseForm):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(BaseForm):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)


class MethodRequest(BaseForm):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    # @property
    # def is_admin(self):
    #     return self.login == ADMIN_LOGIN


def make_method_request(request):
    body = MethodRequest()

    if request['body']['method'] == 'online_score':
        body.arguments = OnlineScoreRequest()
    elif request['body']['method'] == 'clients_interests':
        body.arguments = ClientsInterestsRequest()

    cls = type('Request', (BaseForm,), {'body': body})
    instance = cls.from_iterable(request)
    # instance.body = request['body']
    return instance


class RequestsFabric(object):
    @staticmethod
    def make(handler, request):
        if handler == 'method':
            return make_method_request(request)
        else:
            raise NotImplementedError
