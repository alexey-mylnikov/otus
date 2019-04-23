#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import gzip
import sys
import glob
import logging
import collections
from optparse import OptionParser
# brew install protobuf
# protoc  --python_out=. ./appsinstalled.proto
# pip install protobuf
import appsinstalled_pb2
# pip install python-memcached
import memcache
import time
from multiprocessing import Process, Queue, Pipe, cpu_count
from Queue import Empty

NORMAL_ERR_RATE = 0.01
AppsInstalled = collections.namedtuple("AppsInstalled", ["dev_type", "dev_id", "lat", "lon", "apps", "errs"])
sentinel = object()


def insert_appsinstalled(conn, appsinstalled, dry_run=False):
    ua = appsinstalled_pb2.UserApps()
    ua.lat = appsinstalled.lat
    ua.lon = appsinstalled.lon
    key = "%s:%s" % (appsinstalled.dev_type, appsinstalled.dev_id)
    ua.apps.extend(appsinstalled.apps)
    packed = ua.SerializeToString()
    # @TODO persistent connection
    # @TODO retry and timeouts!
    if not dry_run:
        try:
            return conn.set(key, packed)
        except Exception:
            return 0
    return 1


def parse_appsinstalled(line):
    line_parts = line.split("\t")
    if len(line_parts) < 5:
        return
    dev_type, dev_id, lat, lon, raw_apps = line_parts
    if not dev_type or not dev_id:
        return
    errs = []
    try:
        apps = [int(a.strip()) for a in raw_apps.split(",")]
    except ValueError:
        apps = [int(a.strip()) for a in raw_apps.split(",") if a.isdigit()]
        errs.append('Not all user apps are digits')
    try:
        lat, lon = float(lat), float(lon)
    except ValueError:
        errs.append('Invalid geo coords')
    errs = '{}: {}'.format(line, ', '.join(errs)) if errs else None
    return AppsInstalled(dev_type, dev_id, lat, lon, apps, errs)


def dot_rename(path):
    head, fn = os.path.split(path)
    # atomic in most cases
    os.rename(path, os.path.join(head, "." + fn))


def get_chunk(filename, size=1024*1024):
    with gzip.open(filename, 'rb') as fd:
        while True:
            start = fd.tell()
            fd.seek(size, 1)
            line = fd.readline()
            yield start, fd.tell()
            if not line:
                break


def handle(fdbuffer, memcpool, queue, pipe, dry):
    while True:
        # standby
        if not pipe.poll():
            time.sleep(0.1)
            continue

        cmd = pipe.recv()
        if cmd == 'quit':
            break

        # else keep going
        while True:
            try:
                obj = queue.get(block=False)
            except Empty:
                time.sleep(0.1)
                continue

            # end of file
            if obj is None:
                pipe.send(None)
                break

            filename, chunk = obj
            fd = fdbuffer.get(filename)

            if fd is None:
                fd = gzip.open(filename)
                fdbuffer[filename] = fd

            start, stop = chunk
            fd.seek(start, 0)
            for line in fd:
                line = line.strip()
                if line:
                    app = parse_appsinstalled(line)
                    if not app:
                        pipe.send((1, 'Parse error'))
                        continue
                    conn = memcpool.get(app.dev_type)
                    if not conn:
                        pipe.send((1, 'Unknown device type: {}'.format(app.dev_type)))
                        continue
                    ok = insert_appsinstalled(conn, app, dry)
                    if ok:
                        pipe.send((0, app.errs))
                    else:
                        pipe.send((1, 'Cannot write to memc {}'.format([server.address for server in conn.servers])))

                if fd.tell() == stop:
                    break


def set_fdbuffer(func):
    buf = {}

    def wrapper(*args, **kwargs):
        try:
            return func(buf, *args, **kwargs)
        finally:
            for __, fd in buf.items():
                try:
                    fd.close()
                except Exception:
                    pass
    return wrapper


def set_memcpool(func, options):
    conn_pool = {dev_type: memcache.Client(addr) for dev_type, addr in options.items()}

    def wrapper(*args, **kwargs):
        try:
            return func(conn_pool, *args, **kwargs)
        finally:
            for __, conn in conn_pool.items():
                try:
                    conn.close()
                except Exception:
                    pass
    return wrapper


def run_handler(queue, pipe, memc_conf, dry):
    handler = set_fdbuffer(handle)
    handler = set_memcpool(handler, memc_conf)
    handler(queue, pipe, dry)


def send(workers, command):
    for __, pipe in workers:
        pipe.send(command)


def reap(queue, workers):
    queue.close()
    queue.join_thread()
    for worker, pipe in workers:
        worker.terminate()
        pipe.close()


def spawn(queue, memc_conf, dry):
    parent_conn, child_conn = Pipe(duplex=True)
    process = Process(target=run_handler, args=(queue, child_conn, memc_conf, dry))
    process.daemon = True
    process.start()
    return process, parent_conn


def manage(workers):
    finished = processed = errors = 0
    while all([worker.is_alive() for worker, __ in workers]):
        for __, pipe in workers:
            while pipe.poll():
                obj = pipe.recv()
                if obj is None:
                    finished += 1
                    continue
                code, msg = obj
                if not code:
                    processed += 1
                    if msg:
                        logging.info(msg)
                else:
                    errors += 1
                    logging.error(msg)
        if finished == len(workers):
            break
    else:
        logging.error('Not all workers alive, exiting')
        return

    return processed, errors


def main(options):
    workers, queue = [], Queue()
    memc_conf = {"idfa": [options.idfa], "gaid": [options.gaid],
                 "adid": [options.adid], "dvid": [options.dvid]}
    for __ in range(int(options.processes)):
        workers.append(spawn(queue, memc_conf, options.dry))

    for fn in sorted(glob.iglob(options.pattern)):
        send(workers, 'awake')

        logging.info('Processing: {}'.format(fn))
        for chunk in get_chunk(fn):
            queue.put((fn, chunk))

        # send end of file
        for __ in range(len(workers)):
            queue.put(None)

        result = manage(workers)
        if result is None:
            reap(queue, workers)
            raise RuntimeError

        processed, errors = result
        if processed:
            err_rate = float(errors) / processed
            if err_rate < NORMAL_ERR_RATE:
                logging.info("Acceptable error rate (%s). Successfull load" % err_rate)
            else:
                logging.error("High error rate (%s > %s). Failed load" % (err_rate, NORMAL_ERR_RATE))
        logging.info('{} processed: {}, errors: {}'.format(fn, processed, errors))
        dot_rename(fn)

    send(workers, 'quit')


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
    op.add_option("--pattern", action="store", default="/data/appsinstalled/*.gz")
    op.add_option("--processes", action="store", default=cpu_count())
    op.add_option("--idfa", action="store", default="127.0.0.1:33013")
    op.add_option("--gaid", action="store", default="127.0.0.1:33014")
    op.add_option("--adid", action="store", default="127.0.0.1:33015")
    op.add_option("--dvid", action="store", default="127.0.0.1:33016")
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO if not opts.dry else logging.DEBUG,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')

    logging.info("Memc loader started with options: %s" % opts)
    try:
        main(opts)
    except Exception as e:
        logging.exception("Unexpected error: %s" % e)
        sys.exit(1)
