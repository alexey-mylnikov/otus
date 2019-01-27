#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from api.requests import MethodRequest, OnlineScoreRequest, ClientsInterestsRequest
from api.scoring import get_score, get_interests
from api.consts import (
    ADMIN_SALT, SALT,
    OK, BAD_REQUEST,
    FORBIDDEN, NOT_FOUND,
    INVALID_REQUEST, INTERNAL_ERROR,
    ERRORS
)


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def get_online_score(request, ctx, store):
    arguments = OnlineScoreRequest(request.arguments)
    ctx['has'] = arguments.initialized_fields

    if request.is_admin:
        score = 42
    else:
        score = get_score(
            store=store,
            phone=arguments.phone,
            email=arguments.email,
            birthday=arguments.birthday,
            gender=arguments.gender,
            first_name=arguments.first_name,
            last_name=arguments.last_name
        )

    return {'score': score}


def get_client_interests(request, ctx, store):
    arguments = ClientsInterestsRequest(request.arguments)
    ctx['nclients'] = len(arguments.client_ids)
    return {client_id: get_interests(store, client_id) for client_id in arguments.client_ids}


def method_handler(request, ctx, store):
    try:
        request = MethodRequest(request['body'])
    except (ValueError, TypeError, KeyError) as e:
        return str(e), INVALID_REQUEST

    if not check_auth(request):
        return ERRORS[FORBIDDEN], FORBIDDEN

    if request.method == 'online_score':
        try:
            response, code = get_online_score(request, ctx, store), OK
        except (ValueError, TypeError) as e:
            response, code = str(e), INVALID_REQUEST
    elif request.method == 'clients_interests':
        try:
            response, code = get_client_interests(request, ctx, store), OK
        except (ValueError, TypeError) as e:
            response, code = str(e), INVALID_REQUEST
    else:
        response, code = 'method "{}" not allowed'.format(request.method), INVALID_REQUEST

    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception, e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
