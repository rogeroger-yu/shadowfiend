import sys

from shadowfiend.api import app
from shadowfiend.common import service


def main():
    service.prepare_service(sys.argv)
    server = app.build_server()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
