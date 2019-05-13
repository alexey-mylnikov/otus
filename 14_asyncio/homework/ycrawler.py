import os
import logging
import optparse
import asyncio
import signal
import random


MAIN_PAGE = 'https://news.ycombinator.com/'


async def poll_main_page(loop):
    timeout = random.randint(3, 5)
    await asyncio.sleep(timeout)
    logger.info('sleep {} sec'.format(timeout))


def stop(loop):
    loop.stop()


def callback(future):
    try:
        __ = future.result()
    except Exception as e:
        logging.exception(e)


def schedule_poll(loop, period):
    loop.call_later(period, schedule_poll, loop, period)
    future = asyncio.ensure_future(poll_main_page(loop))
    future.add_done_callback(callback)


if __name__ == '__main__':
    op = optparse.OptionParser()
    op.add_option("--root", action="store", default='.')
    op.add_option("--period", action="store", type=int, default=1)
    op.add_option("--log-file", action="store", default=None)
    op.add_option("--log-level", action="store", default='INFO')
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log_file,
                        level=logging.getLevelName(opts.log_level),
                        format='[%(asctime)s] [%(name)s] [%(levelname).1s] %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')
    logger = logging.getLogger('ycrawler')
    os.chdir(opts.root)
    eloop = asyncio.get_event_loop()
    eloop.add_signal_handler(getattr(signal, 'SIGINT'), stop, eloop)
    eloop.add_signal_handler(getattr(signal, 'SIGTERM'), stop, eloop)
    eloop.call_soon(schedule_poll, eloop, opts.period)

    try:
        eloop.run_forever()
    finally:
        eloop.close()


