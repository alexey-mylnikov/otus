from src.server import HTTPServer


if __name__ == '__main__':
    s = HTTPServer()
    s.serve_forever()
