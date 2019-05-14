import os
import logging
import optparse
import asyncio
import signal
import aiohttp
from html.parser import HTMLParser


MAIN_PAGE = 'https://news.ycombinator.com/'


class MainParser(HTMLParser):
    def __init__(self, *args, **kwargs):
        super(MainParser, self).__init__(*args, **kwargs)
        self.target = None

    def handle_starttag(self, tag, attrs):
        self.target.send(('start', (tag, attrs)))

    def handle_endtag(self, tag):
        self.target.send(('end', tag))


async def poll_main_page(loop):
    parser = MainParser()

    async with aiohttp.ClientSession(loop=loop, raise_for_status=True) as session:
        async with lock:
            async with session.get(MAIN_PAGE) as resp:
                parser.feed(await resp.text())


def stop(loop):
    loop.stop()


def callback(future):
    try:
        __ = future.result()
    except Exception as e:
        logger.exception(e)


def schedule_poll(loop, period):
    loop.call_later(period, schedule_poll, loop, period)
    future = asyncio.ensure_future(poll_main_page(loop))
    future.add_done_callback(callback)


if __name__ == '__main__':
    op = optparse.OptionParser()
    op.add_option("--root", action="store", default='.')
    op.add_option("--period", action="store", type=int, default=5)
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
    lock = asyncio.Lock(loop=eloop)
    eloop.call_soon(schedule_poll, eloop, opts.period)

    try:
        eloop.run_forever()
    finally:
        eloop.close()
