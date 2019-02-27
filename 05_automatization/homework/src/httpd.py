import io
import socket
import struct
from src import asyncore

struct_L = struct.Struct('<Q')


class BaseHandler(asyncore.dispatcher_with_send):
    def handle_read(self):
        size = 0

        with io.BytesIO() as buf:
            while True:
                resp = self.recv(1024)

                if resp:
                    size += buf.write(resp)

                print(size, buf.getvalue())
                return


class BaseServer(asyncore.dispatcher):
    def __init__(self, addr='127.0.0.1', port=5000, timeout=1, backlog=5):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((addr, port))

        super(BaseServer, self).__init__(sock)

        self.timeout = timeout
        self.backlog = backlog

    def serve_forever(self):
        self.listen(num=self.backlog)
        asyncore.loop(timeout=self.timeout)

    def handle_accepted(self, sock, addr):
        BaseHandler(sock=sock)


if __name__ == '__main__':
    s = BaseServer()
    s.serve_forever()
