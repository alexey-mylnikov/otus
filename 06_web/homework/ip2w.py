import os
import re
import json
import requests
import logging
from functools import reduce


logging.basicConfig(
    level=logging.getLevelName(os.getenv('LOG_LEVEL', 'INFO')),
    format='[%(asctime)s] [%(name)s] [%(levelname).1s] %(message)s',
    datefmt='%Y.%m.%d %H:%M:%S'
)
logger = logging.getLogger('ip2w')


def not_found(environ, start_response):
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return ['404 Not Found']


def handle_internal_errors(handler):
    def wrapper(environ, start_response):
        try:
            return handler(environ, start_response)
        except Exception as e:
            logger.exception(e)
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return ['500 Internal Server Error']
    return wrapper


def handle_not_found(handler):
    def wrapper(environ, start_response):
        method = environ['REQUEST_METHOD'].upper()
        path = environ.get('PATH_INFO', '/')
        if method == 'GET':
            match = re.match(r'/ip2w/(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', path)
            if match:
                environ['QUERY_PARAMS'] = match.groupdict()
                return handler(environ, start_response)
        return not_found(environ, start_response)
    return wrapper


def fetch_geo(ip):
    resp = requests.get('https://ipinfo.io/{}/geo'.format(ip))
    if resp.status_code == 404:
        logger.warning('ip info not found for: {}'.format(ip))
        return None
    resp.raise_for_status()
    return resp.json()


def fetch_weather(country, city, **kwargs):
    kwargs.update({'q': '{},{}'.format(city, country)})
    resp = requests.get('https://api.openweathermap.org/data/2.5/weather', params=kwargs)
    if resp.status_code == 404:
        logger.warning('weather not found for: {} {}'.format(country, city))
        return None
    resp.raise_for_status()
    return resp.json()


def app(environ, start_response):
    geo = fetch_geo(environ['QUERY_PARAMS']['ip'])
    if geo is None:
        return not_found(environ, start_response)

    if geo.get('bogon'):
        start_response('200 OK', [('Content-Type', 'application/json')])
        return json.dumps({'error': 'bogus address'})

    weather = fetch_weather(geo['city'], geo['country'], units='metric', appid=os.getenv('OPENWEATHER_TOKEN'))
    if weather is None:
        return not_found(environ, start_response)

    start_response('200 OK', [('Content-Type', 'application/json')])
    return json.dumps({'city': geo['city'], 'temp': weather['main']['temp'],
                       'conditions': weather['weather'][0]['description']})


middlewares = [handle_internal_errors, handle_not_found]
application = reduce(lambda h, m: m(h), middlewares, app)
