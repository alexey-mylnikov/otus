import os
import logging
import optparse
import asyncio
import signal
import aiohttp
import shutil
import concurrent.futures
import html.parser
from collections import namedtuple


PATIENCE = 60
MAIN_PAGE = 'https://news.ycombinator.com/'
News = namedtuple('News', ['id', 'title', 'href'])
lock = asyncio.Lock()


class Parser(html.parser.HTMLParser):
    def __init__(self, target):
        super(Parser, self).__init__()
        self.target = target

    def handle_starttag(self, tag, attrs):
        self.target.send(('start', (tag, attrs)))

    def handle_endtag(self, tag):
        self.target.send(('end', tag))

    def handle_data(self, data):
        self.target.send(('data', data))


def coroutine(func):
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        cr.__next__()
        return cr
    return start


def stop(loop):
    loop.stop()


def callback(future):
    try:
        __ = future.result()
    except Exception as e:
        logger.exception(e)


def create_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
        return True
    return False


async def upload_news(loop, news):
    with concurrent.futures.ThreadPoolExecutor() as pool:
        async with lock:
            created = await loop.run_in_executor(pool, create_if_not_exists, '{}/comments'.format(news.id))


@coroutine
def schedule_news_upload(loop):
    while True:
        news = (yield)
        future = asyncio.ensure_future(upload_news(loop, news))
        future.add_done_callback(callback)


@coroutine
def parse_main_page(target):
    # search athing
    while True:
        event, value = (yield)
        if event == 'start' and value[0] == 'tr':
            attrs = {key: value for key, value in value[1]}
            if attrs.get('class') == 'athing':
                news = {'id': attrs['id']}

                # search storylink
                while True:
                    event, value = (yield)
                    if event == 'start' and value[0] == 'a':
                        attrs = {key: value for key, value in value[1]}
                        if attrs.get('class') == 'storylink':
                            news['href'] = attrs['href']

                            # get data
                            event, value = (yield)
                            assert event == 'data', 'Unexpected event'

                            news['title'] = value
                            target.send(News(**news))
                            break


async def poll_main_page(loop):
    parser = Parser(parse_main_page(schedule_news_upload(loop)))
    async with aiohttp.TCPConnector(ssl=None) as conn:
        async with aiohttp.ClientSession(connector=conn, loop=loop, raise_for_status=True) as session:
            async with session.get(MAIN_PAGE) as resp:
                parser.feed(await resp.text())


def schedule_main_page_poll(loop, period):
    loop.call_later(period, schedule_main_page_poll, loop, period)
    future = asyncio.ensure_future(poll_main_page(loop))
    future.add_done_callback(callback)


if __name__ == '__main__':
    op = optparse.OptionParser()
    op.add_option("--root", action="store", default='.')
    op.add_option("--period", action="store", type=int, default=30)
    op.add_option("--log-file", action="store", default=None)
    op.add_option("--log-level", action="store", default='INFO')
    (opts, args) = op.parse_args()
    os.chdir(opts.root)

    logging.basicConfig(filename=opts.log_file,
                        format='[%(asctime)s] [%(name)s] [%(levelname).1s] %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')
    logger = logging.getLogger('ycrawler')
    logger.setLevel(level=logging.getLevelName(opts.log_level))

    eloop = asyncio.get_event_loop()
    eloop.add_signal_handler(getattr(signal, 'SIGINT'), stop, eloop)
    eloop.add_signal_handler(getattr(signal, 'SIGTERM'), stop, eloop)
    eloop.call_soon(schedule_main_page_poll, eloop, opts.period)

    try:
        eloop.run_forever()
    finally:
        eloop.close()
