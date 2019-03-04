import os
import io
import socket
import asyncore_epoll
from urllib.parse import unquote_to_bytes

CRLF = b'\r\n'
CHUNK = 1024


class InvalidRequest(Exception):
    pass


class HTTPHandler(asyncore_epoll.dispatcher):
    available_proto = frozenset(('HTTP/1.0', 'HTTP/1.1'))

    def __init__(self, sock):
        super(HTTPHandler, self).__init__(sock)

        self.method = None
        self.path = None
        self.proto = None
        self.header = {}

        self.in_buffer = io.BytesIO()
        self.out_buffer = io.BytesIO()

    def parse_header(self, data):
        lines = [line.strip() for line in data.split(CRLF) if line.strip()]

        if not lines:
            raise InvalidRequest('empty header')

        status_line = lines.pop(0)
        parts = status_line.split()

        if len(parts) != 3:
            raise InvalidRequest('invalid status line {}'.format(status_line))

        self.method, self.path, self.proto = parts

        # try:
        #     self.path = os.path.normpath(unquote_to_bytes(path))
        # except ValueError:
        #     raise InvalidRequest('invalid path {}'.format(path))
        #
        # if self.proto not in self.available_proto:
        #     raise InvalidRequest('protocol not available {}'.format(self.proto))

        errors = []

        for line in lines:
            parts = line.split(b':', 1)
            if len(parts) != 2:
                errors.append(line)
            else:
                self.header[parts[0].strip()] = parts[1].strip()

        if errors:
            raise InvalidRequest('invalid header {}'.format(', '.join(errors)))

    def read_header(self):
        cur = None
        raw = None
        old = self.in_buffer.tell()
        end = self.in_buffer.getbuffer().nbytes

        self.in_buffer.seek(0, os.SEEK_SET)

        while True:
            if self.in_buffer.readline() == CRLF:
                cur = self.in_buffer.tell() - len(CRLF)
                break

            if self.in_buffer.tell() == end:
                break

        if cur is not None:
            self.in_buffer.seek(0, os.SEEK_SET)
            raw = self.in_buffer.read(cur)
            self.in_buffer.seek(old, os.SEEK_SET)

        return raw

    def handle_read(self):
        data = self.recv(CHUNK)

        if not data:
            return

        self.in_buffer.write(data)

        data = self.read_header()
        if data:
            try:
                self.set_header()
            except InvalidRequest:
                return  # TODO: write bad request in out buffer

        # cause we know, there is no body
        self.out_buffer.write(b'HTTP/1.1 200\r\n\r\nok, but what now?')
        self.out_buffer.seek(0, os.SEEK_SET)

    def initiate_send(self):
        self.socket.sendall(self.out_buffer.read())

    def handle_write(self):
        self.initiate_send()
        self.close()

    def writable(self):
        return (not self.connected) or (self.out_buffer.tell() != self.out_buffer.getbuffer().nbytes)

    def send(self, data):
        old = self.out_buffer.tell()
        self.out_buffer.seek(0, os.SEEK_END)
        self.out_buffer.write(data)
        self.out_buffer.seek(old, os.SEEK_SET)
        self.initiate_send()


class HTTPServer(asyncore_epoll.dispatcher):
    def __init__(self, addr='127.0.0.1', port=5000, backlog=5, poll_interval=0.5):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((addr, port))

        super(HTTPServer, self).__init__(sock)

        self.backlog = backlog
        self.poll_interval = poll_interval

    def serve_forever(self):
        self.listen(num=self.backlog)
        asyncore_epoll.loop(timeout=self.poll_interval)

    def handle_accepted(self, sock, addr):
        HTTPHandler(sock=sock)
