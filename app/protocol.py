from abc import abstractmethod, ABC
import asyncio
import json
import pickle
import socket


class BaseProtocol(ABC):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    @abstractmethod
    def read(self, *args, **kwargs):
        pass

    @abstractmethod
    def write(self, *args, **kwargs):
        pass


class TransportProtocol(BaseProtocol):
    def read(self, conn, encoding='utf-8', nbits=1024, char_end=b'\n', pickle_load=True):
        result, data = {}, b''

        while not data.endswith(char_end):
            try:
                data += conn.recv(nbits)
            except (ConnectionError, OSError) as e:
                conn.close()
                raise ConnectionError(e)

        try:
            result = data
            if pickle_load:
                result = pickle.loads(result, encoding=encoding)
        except json.JSONDecodeError:
            pass

        return result

    def write(self, data, conn, nbits=1024, char_end=b'\n'):
        try:
            conn.send(pickle.dumps(data) + char_end)
        except (ConnectionError, OSError) as e:
            conn.close()
            raise ConnectionError(e)

    async def aread(self, conn, loop=None, encoding='utf-8', nbits=1024, char_end=b'\n'):
        loop = loop or asyncio.get_event_loop()
        result, data = {}, b''

        while not data.endswith(char_end):
            try:
                data += await loop.sock_recv(conn, nbits)
            except (ConnectionError, OSError) as e:
                conn.close()
                raise ConnectionError(e)

        try:
            result = pickle.loads(data, encoding=encoding)
        except json.JSONDecodeError:
            pass

        return result


########################################################################################################################
# SOCKETS PROTOCOLS
########################################################################################################################

class SocketProtocol(TransportProtocol):
    def __init__(self, loop=None, *args, **kwargs):
        self._socket = socket.socket(*args, **kwargs)
        self._loop = loop or asyncio.get_event_loop()

        super().__init__(loop, *args, **kwargs)

        self.is_active = False
        self.accept_callback = lambda *_: _
        self.echo_task = None

    def read(self, conn=None, encoding='utf-8', nbits=1024, char_end=b'\n', pickle_load=True):
        conn = conn or self._socket
        result = super().read(conn, encoding, nbits, char_end, pickle_load)

        return result

    def write(self, data, conn=None, nbits=1024, char_end=b'\n'):
        conn = conn or self._socket
        result = super().write(data, conn, nbits, char_end)

        return result

    def run_echo_server(self, host, port, accept_callback=None, queue_length=5):
        """ Sets up a port listener and starts tasks to listen for incoming connections in an event loop.  """

        self.accept_callback = accept_callback or self.accept_callback

        self._socket.bind((host, int(port)))
        self._socket.listen(queue_length)

        self.is_active = True

        self.echo_task = self._loop.create_task(self._echo(), name='socket_server__echo')

    async def _echo(self):
        """ Creates tasks for processing incoming connections asynchronously.  """

        while self.is_active:
            try:
                connection, address = await self._loop.sock_accept(self._socket)
            except OSError as e:
                break
            self._loop.create_task(self.accept_callback(connection, address), name='socket_server__accept_callback')

    async def accept_callback(self, connection, address, *args, **kwargs):
        pass

    def server_stop(self):
        self.is_active = False
        self._socket.close()
        del self.echo_task

    def connect(self, host, port, timeout=None):
        if timeout is not None:
            self._socket.settimeout(float(timeout))
        self._socket.connect((host, int(port)))
        self.is_active = True

    def disconnect(self):
        self.is_active = False
        self._socket.close()
