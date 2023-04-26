import asyncio
import time

from services.common import Service


TIME_PATTERN = '%Y.%m.%d %H:%M'


def authenticate(data_json, auth_mode):
    return 'ok'


def auth_required(func):
    async def wrapped(self, conn, data_json):
        is_identified = conn.fileno in self.connections

        return await func(self, conn, data_json) if is_identified else None

    return wrapped


class MessageService(Service):
    DEFAULT_USER = 'anonymous'

    def __init__(self, service_id, proto, host=None, port=None, allow_multisession=False, **kwargs):
        super().__init__(service_id, proto, host, port, **kwargs)
        self.history = []
        self.allow_multisession = allow_multisession

        # Protocol method handlers
        self.receivers = {
            'connect': self._transport_connect,
            'auth': self._transport_auth,
            'close': self._transport_close,
            'send': self._transport_send,
            'cmd': self._transport_cmd
        }

        # Chat member dictionary in the format: {<member fileno>: <member transport>}
        # Also the username is stored in <member writer> value
        self.connections = {}
        self.usernames = {}

    async def accept_callback(self, connection, address):
        try:
            # Sending services metadata
            # Waiting for authentication data from client
            data_json = await self.proto.aread(connection, self.loop)
            if data_json['type'] != 'connect':
                return
            await self._transport_connect(connection, data_json)

            # Sending chat history
            data = '\n'.join(['({timestamp}) {user}: {data}'.format(**row) for row in self.history])
            chat_history_response = {'type': 'send', 'data': data}
            self.proto.write(chat_history_response, connection)

            # Listening to incoming messages from the client
            while self.is_active:
                data_json = await self.proto.aread(connection, self.loop)
                await self.receivers[data_json['type']](connection, data_json)

        except ConnectionError as e:
            pass
        finally:
            if connection.fileno in self.connections:
                await self._transport_close(connection)

    def stop(self):
        self.is_active = False

        for transport in self.connections.values():
            transport.close()
        #self._socket.shutdown(socket.SHUT_RDWR)
        self.proto.server_stop()

    async def _transport_connect(self, connection, data_json):
        """ Processes an incoming connect request.  """

        data_json['status'] = 'auth'
        data_json['authentication'] = None or ''

        self.proto.write(data_json, connection)
        connect_data = await self.proto.aread(connection, self.loop)
        await self._transport_auth(connection, connect_data)

    async def _transport_auth(self, connection, data_json):
        username = data_json.get('username') or self.DEFAULT_USER
        auth_status = None
        is_occupied = None

        if username and None in ['username', 'password']:
            is_occupied = username in [writer.username for writer in self.connections.values()]

        if not self.allow_multisession and is_occupied:
            auth_status = 'multi session error'

        auth_status = auth_status or authenticate(data_json, None)

        data_json['status'] = auth_status
        data_json['username'] = username
        self.proto.write(data_json, connection)

        if auth_status == 'ok':
            self.usernames[connection.fileno] = username
            self.connections[connection.fileno] = connection
        else:
            await self._transport_close(connection)

    async def _transport_close(self, connection, *args):
        """ Processes an incoming close connection request.  """

        if connection.fileno in self.connections:
            self.connections.pop(connection.fileno)

        connection.close()

    @auth_required
    async def _transport_send(self, connection, data_json):
        """ Processes an incoming request to send a message.  """

        row = {
            'user': self.usernames[connection.fileno],
            'data': data_json.get('data'),
            'timestamp': time.strftime(TIME_PATTERN)
        }

        self.history.append(row)

        # A new message is sent as a list
        data_json['data'] = '({timestamp}) {user}: {data}'.format(**row)
        for connection in self.connections.values():
            self.proto.write(data_json, connection)

    @auth_required
    async def _transport_cmd(self, transport, data_json):
        self.is_active = False
