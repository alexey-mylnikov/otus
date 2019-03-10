import os
import sys
import time
import socket
import signal
import logging
import argparse
import asyncore_epoll
from io import BytesIO
from mimetypes import guess_type
from urllib.parse import unquote, urlparse
from utils import httpdate

CRLF = b'\r\n'
ENCODING = 'UTF-8'

UMASK = 0o22
REDIRECT_TO = getattr(os, 'devnull', '/dev/null')
SERVER = 'MyServer'

OK = 200
BAD_REQUEST = 400
NOT_FOUND = 404
NOT_ALLOWED = 405
INVALID_REQUEST = 422
INTERNAL_ERROR = 500

ERRORS = {
    BAD_REQUEST: 'Bad Request',
    NOT_FOUND: 'Not Found',
    NOT_ALLOWED: 'Method Not Allowed',
    INVALID_REQUEST: 'Invalid Request',
    INTERNAL_ERROR: 'Internal Server Error',
}


class InvalidRequest(Exception):
    pass


class Request(object):
    def __init__(self, version=None, method=None, path=None, params=None, headers=None):
        self.method = method
        self.path = path
        self.params = params
        self.version = version
        self.headers = headers or {}


class ContentFile(object):
    def __init__(self, path):
        self.path = path

    @property
    def content(self):
        with open(self.path, 'rb') as f:
            return f.read()

    @property
    def meta(self):
        content_type = guess_type(self.path)
        if isinstance(content_type, tuple):
            content_type = content_type[0]
        return {'Content-Type': content_type, 'Content-Length': os.path.getsize(self.path)}


class Response(object):
    versions = frozenset(['HTTP/1.1', 'HTTP/1.0'])

    def __init__(self, code, text):
        self._version = list(self.versions)[0]
        self.code = code
        self.text = text
        self.headers = {}
        self._content = b''

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        if self._version not in self.versions:
            raise ValueError('only versions available {}'.format(self.versions))
        self._version = value

    @property
    def header(self):
        status_line = '{} {} {}\r\n'.format(self.version, self.code, self.text)
        headers = ''.join(['{}: {}\r\n'.format(k, v) for k, v in self.headers.items()])
        return ''.join([status_line, headers, '\r\n']).encode(ENCODING)

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        if isinstance(value, bytearray):
            raise ValueError('content must be bytes')
        self._content = value

    @content.deleter
    def content(self):
        self._content = b''
        __ = self.headers.pop('Content-Type', None)
        __ = self.headers.pop('Content-Length', None)


class Buffer(BytesIO):
    def __len__(self):
        return self.getbuffer().nbytes

    def append(self, data):
        old = self.tell()
        self.seek(0, os.SEEK_END)
        count = self.write(data)
        self.seek(old, os.SEEK_SET)
        return count


class Handler(asyncore_epoll.dispatcher):
    versions = frozenset(['HTTP/1.1', 'HTTP/1.0'])
    index_file = 'index.html'

    def __init__(self, sock):
        super(Handler, self).__init__(sock)

        self.request = Request()
        self.in_buffer = Buffer()
        self.out_buffer = Buffer()

    def get_file(self):
        path = self.request.path.lstrip('/')

        if os.path.isdir(path):
            path = os.path.join(path, self.index_file)

        if os.path.isfile(path):
            return ContentFile(path)

    def get(self):
        file = self.get_file()

        if not file:
            return Response(NOT_FOUND, ERRORS[NOT_FOUND])

        response = Response(OK, 'OK')
        response.content = file.content
        response.headers.update(file.meta)
        return response

    def head(self):
        file = self.get_file()

        if not file:
            return Response(NOT_FOUND, ERRORS[NOT_FOUND])

        response = Response(OK, 'OK')
        response.headers.update(file.meta)
        return response

    def parse_status_line(self, line):
        parts = line.split()

        if len(parts) != 3:
            raise InvalidRequest()

        self.request.method = parts[0]
        uri = urlparse(parts[1])
        self.request.path = os.path.normpath(unquote(uri.path))
        self.request.params = uri.params
        proto = parts[2]

        if proto not in self.versions:
            raise InvalidRequest()

        self.request.version = proto

    def parse_headers(self, lines):
        errors = []

        for line in lines:
            parts = line.split(':', 1)
            if len(parts) != 2:
                errors.append(line)
            else:
                self.request.headers[parts[0].strip()] = parts[1].strip()

        if errors:
            raise InvalidRequest()

    def parse(self):
        raw = self.in_buffer.getvalue()
        lines = [line.strip().decode(ENCODING) for line in raw.split(CRLF) if line.strip()]

        if not lines:
            raise InvalidRequest()

        self.parse_status_line(lines.pop(0))
        self.parse_headers(lines)

    def _handle(self):
        try:
            self.parse()
        except InvalidRequest:
            return Response(INVALID_REQUEST, ERRORS[INVALID_REQUEST])
        except Exception as e:
            return Response(INTERNAL_ERROR, ERRORS[INVALID_REQUEST])

        handler = getattr(self, self.request.method.lower(), None)

        if not handler:
            return Response(NOT_ALLOWED, ERRORS[NOT_ALLOWED])

        try:
            return handler()
        except Exception as e:
            return Response(INTERNAL_ERROR, ERRORS[INTERNAL_ERROR])

    def handle(self):
        response = self._handle()
        response.version = self.request.version
        response.headers['Server'] = SERVER
        response.headers['Date'] = httpdate()
        response.headers['Connection'] = 'close'
        return response

    def end_of_data(self):
        res = False
        buf = self.in_buffer
        old = buf.tell()
        end = len(buf)

        buf.seek(0, os.SEEK_SET)

        while buf.tell() < end:
            if buf.readline() == CRLF:
                res = True
                break

        buf.seek(old, os.SEEK_SET)
        return res

    def handle_read(self):
        end_of_data = self.end_of_data

        while not end_of_data():
            chunk = self.in_buffer.append(self.recv(1024))
            if not chunk:
                return  # connection was closed

        response = self.handle()
        self.out_buffer.append(response.header)
        self.out_buffer.append(response.content)

    def handle_write(self):
        cur = self.out_buffer.tell()
        cur += self.send(self.out_buffer.read(1024))
        self.out_buffer.seek(cur, os.SEEK_SET)

    def writable(self):
        return (not self.connected) or (self.out_buffer.tell() != len(self.out_buffer))


class Worker(asyncore_epoll.dispatcher):
    def __init__(self, addr, handler_class, backlog, poll_interval):
        self.handler = handler_class
        self.backlog = backlog
        self.poll_interval = poll_interval

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(addr)
        super(Worker, self).__init__(sock)

    def run(self):
        self.listen(num=self.backlog)
        asyncore_epoll.loop(timeout=self.poll_interval, poller=asyncore_epoll.epoll_poller)

    def handle_accepted(self, sock, addr):
        self.handler(sock=sock)


class HTTPServer(object):
    def __init__(self, addr, handler_class, workers, backlog=5, poll_interval=0.5):
        self.addr = addr
        self.handler = handler_class
        self.workers = workers
        self.backlog = backlog
        self.poll_interval = poll_interval
        self.workers_map = []

    def spawn_worker(self):
        worker = Worker(self.addr, self.handler, self.backlog, self.poll_interval)

        pid = os.fork()

        # main (parent) process
        if pid != 0:
            self.workers_map.append(pid)
            logging.info('booting worker, pid {}'.format(pid))
            return

        # worker (child) process
        os.setsid()
        os.umask(UMASK)

        for fd in range(0, 3):
            try:
                os.close(fd)
            except OSError:
                pass

        fd_null = os.open(REDIRECT_TO, os.O_RDWR)

        if fd_null != 0:
            os.dup2(fd_null, 0)

        os.dup2(0, 1)
        os.dup2(0, 2)

        worker.run()

    def kill_workers(self):
        for pid in self.workers_map:
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass

    def serve_forever(self):
        for i in range(self.workers):
            self.spawn_worker()

        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            logging.info('shutdown')
        finally:
            self.kill_workers()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname).1s] %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
        stream=sys.stdout
    )

    ap = argparse.ArgumentParser()
    ap.add_argument('-a', '--address', action='store', default='localhost')
    ap.add_argument('-p', '--port', action='store', type=int, default=8080)
    ap.add_argument('-r', '--document-root', action='store', default='/var/www')
    ap.add_argument('-w', '--workers', action='store', type=int, default=4)
    args = ap.parse_args()

    os.chdir(args.document_root)
    logging.info('starting server at {}:{}, pid {}'.format(args.address, args.port, os.getpid()))

    server = HTTPServer((args.address, args.port), Handler, workers=args.workers)
    server.serve_forever()
