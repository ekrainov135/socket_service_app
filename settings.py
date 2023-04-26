import logging
import socket

from app.protocol import SocketProtocol
from services import ManagerService, FileTransferService, MessageService


APP_NAME = 'socket_services'


# Logging
LOG_FILE_PATH = 'logs/server.log'
LOG_TEXT_FORMAT = '%(levelname)s [%(asctime)s] %(name)s: %(message)s'

logging.basicConfig(level=logging.DEBUG, filename=LOG_FILE_PATH, format=LOG_TEXT_FORMAT)

server_logger = logging.getLogger(APP_NAME)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('%(name)s: %(message)s', '%m.%d %X'))

server_logger.addHandler(stream_handler)


# Services
SERVICES = {
    ('127.0.0.1', 7070): [ManagerService, SocketProtocol(family=socket.AF_INET, type=socket.SOCK_STREAM)],
    ('127.0.0.1', 7071): [FileTransferService, SocketProtocol(family=socket.AF_INET, type=socket.SOCK_STREAM)],
    ('127.0.0.1', 7072): [MessageService, SocketProtocol(family=socket.AF_INET, type=socket.SOCK_STREAM)],
}
