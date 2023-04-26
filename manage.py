import sys

from app.server import Server
from settings import SERVICES


def run_service_server():
    services = []

    for idx, service_meta in enumerate(SERVICES.items()):
        host, port = service_meta[0]
        service, proto = service_meta[1]
        services.append(service(idx, proto, host=host, port=port))

    server = Server(services)
    try:
        server.run()
    except KeyboardInterrupt:
        server.abort()


def main():
    handlers = {
        'run': run_service_server,
    }

    console_command = 'run' if len(sys.argv) == 1 else sys.argv[1]
    try:
        handlers[console_command](*sys.argv[2:])
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
