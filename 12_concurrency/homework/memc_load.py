#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import gzip
import sys
import glob
import time
import logging
import collections
from optparse import OptionParser
# brew install protobuf
# protoc  --python_out=. ./appsinstalled.proto
# pip install protobuf
import appsinstalled_pb2
# pip install python-memcached
import memcache
import multiprocessing
import contextlib

SOCKET_TIMEOUT = 30
RETRY = 3
BACKOFF = 0.2

EMPTY = (0, 0)
SUCCESS = (1, 0)
ERROR = (0, 1)

NORMAL_ERR_RATE = 0.01

AppsInstalled = collections.namedtuple("AppsInstalled", ["dev_type", "dev_id", "lat", "lon", "apps"])


class DummyClient(object):
    def __init__(self, servers, *args, **kwargs):
        self.servers = servers
        self.unpacked = appsinstalled_pb2.UserApps()

    def set(self, key, val, *args, **kwargs):
        logging.debug("%s - %s -> %s" % (
            self.servers, key, str(self.unpacked.ParseFromString(val)).replace("\n", " ")))
        return True


def init_conn(memc_addr, timeout=SOCKET_TIMEOUT, dry_run=False):
    global connections
    memc = DummyClient if dry_run else memcache.Client
    connections = {dev: memc([addr], dead_retry=0, socket_timeout=timeout) for dev, addr in memc_addr.items()}


def insert_appsinstalled(client, appsinstalled):
    ua = appsinstalled_pb2.UserApps()
    ua.lat = appsinstalled.lat
    ua.lon = appsinstalled.lon
    key = "%s:%s" % (appsinstalled.dev_type, appsinstalled.dev_id)
    ua.apps.extend(appsinstalled.apps)
    packed = ua.SerializeToString()

    total = remain = RETRY
    success = 0

    while not success and remain > 0:
        try:
            success = client.set(key, packed)
        except Exception as e:
            logging.exception("Cannot write to memc %s: %s" % (client.servers, e))
            time.sleep(BACKOFF * (2 ** (total - remain)))
            remain -= 1

    return success


def parse_appsinstalled(line):
    line_parts = line.split("\t")
    if len(line_parts) < 5:
        return
    dev_type, dev_id, lat, lon, raw_apps = line_parts
    if not dev_type or not dev_id:
        return
    try:
        apps = [int(a.strip()) for a in raw_apps.split(",")]
    except ValueError:
        apps = [int(a.strip()) for a in raw_apps.split(",") if a.isidigit()]
        logging.info("Not all user apps are digits: `%s`" % line)
    try:
        lat, lon = float(lat), float(lon)
    except ValueError:
        logging.info("Invalid geo coords: `%s`" % line)
    return AppsInstalled(dev_type, dev_id, lat, lon, apps)


def parse(line):
    line = line.strip()
    if not line:
        return EMPTY

    appsinstalled = parse_appsinstalled(line)
    if not appsinstalled:
        return ERROR

    client = connections.get(appsinstalled.dev_type)
    if not client:
        logging.error("Unknow device type: %s" % appsinstalled.dev_type)
        return ERROR

    return SUCCESS if insert_appsinstalled(client, appsinstalled) else ERROR


def dot_rename(path):
    head, fn = os.path.split(path)
    # atomic in most cases
    os.rename(path, os.path.join(head, "." + fn))


@contextlib.contextmanager
def mpool(*args, **kwargs):
    pool = multiprocessing.Pool(*args, **kwargs)
    yield pool
    pool.terminate()


def main(options):
    device_memc = {
        "idfa": options.idfa,
        "gaid": options.gaid,
        "adid": options.adid,
        "dvid": options.dvid,
    }

    params = {
        'processes': options.processes,
        'initializer': init_conn,
        'initargs': (device_memc, options.timeout, options.dry)
    }

    with mpool(**params) as pool:
        for fn in glob.iglob(options.pattern):
            logging.info('Processing %s' % fn)
            with gzip.open(fn) as gz:
                res = pool.imap(func=parse, iterable=gz)
                processed, errors = [sum(x) for x in zip(*res)]

                if processed:
                    err_rate = float(errors) / processed
                    if err_rate < NORMAL_ERR_RATE:
                        logging.info("Acceptable error rate (%s). Successfull load" % err_rate)
                    else:
                        logging.error("High error rate (%s > %s). Failed load" % (err_rate, NORMAL_ERR_RATE))

            dot_rename(fn)


def prototest():
    sample = "idfa\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,43,567,3,7,23\ngaid\t7rfw452y52g2gq4g\t55.55\t42.42\t7423,424"
    for line in sample.splitlines():
        dev_type, dev_id, lat, lon, raw_apps = line.strip().split("\t")
        apps = [int(a) for a in raw_apps.split(",") if a.isdigit()]
        lat, lon = float(lat), float(lon)
        ua = appsinstalled_pb2.UserApps()
        ua.lat = lat
        ua.lon = lon
        ua.apps.extend(apps)
        packed = ua.SerializeToString()
        unpacked = appsinstalled_pb2.UserApps()
        unpacked.ParseFromString(packed)
        assert ua == unpacked


if __name__ == '__main__':
    op = OptionParser()
    op.add_option("-t", "--test", action="store_true", default=False)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("--dry", action="store_true", default=False)
    op.add_option("--pattern", action="store", default="/data/appsinstalled/*.tsv.gz")
    op.add_option("--processes", action="store", type=int, default=multiprocessing.cpu_count())
    op.add_option("--timeout", action="store", type=int, default=30)
    op.add_option("--idfa", action="store", default="127.0.0.1:33013")
    op.add_option("--gaid", action="store", default="127.0.0.1:33014")
    op.add_option("--adid", action="store", default="127.0.0.1:33015")
    op.add_option("--dvid", action="store", default="127.0.0.1:33016")
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO if not opts.dry else logging.DEBUG,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    if opts.test:
        prototest()
        sys.exit(0)

    logging.info("Memc loader started with options: %s" % opts)
    try:
        main(opts)
    except Exception as e:
        logging.exception("Unexpected error: %s" % e)
        sys.exit(1)
