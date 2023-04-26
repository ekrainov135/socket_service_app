import os.path
from abc import abstractmethod, ABC
import pickle
import time


CLEARING_STRING = "\033[A{}\033[A".format(' '*100)


class BaseClient(ABC):
    CLIENT_DIR = 'client'
    HOSTS_DIR = os.path.join(CLIENT_DIR, 'hosts')
    handlers = {}

    def __init__(self, proto):
        self.proto = proto
        self.auth_mode = None
        self.username = None

    def echo_server(self):
        while True:
            try:
                response = self.proto.read()
                if response['type'] in self.handlers:
                    self.handlers[response['type']](response)
            except ConnectionError:
                break

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

    def auth(self, *args, **kwargs):
        pass


class ManagerServiceClient(BaseClient):
    """ An object for communicating with the main service manager of the server and receiving meta-information.  """

    def run(self, host, port, update_meta=True):

        if update_meta or not os.path.exists(self.HOSTS_DIR):
            self.proto.connect(host, int(port))
            server_metadata = self.proto.read(pickle_load=False)
            self.proto.disconnect()

            with open(self.HOSTS_DIR, 'wb') as file:
                file.write(server_metadata)
        else:
            with open(self.HOSTS_DIR, 'rb') as file:
                server_metadata = file.read()

        server_metadata = pickle.loads(server_metadata, encoding='utf-8')

        for service_name, service_meta in server_metadata.items():
            print('{:<20} {}'.format(service_name, str(service_meta)))


class MessageServiceClient(BaseClient):
    """ An object for communicating with the main service manager of the server and receiving meta-information.  """

    def __init__(self, proto):
        super().__init__(proto)
        self.handlers = {'send': self._send}

    def run(self, host, port):
        self.proto.connect(host, port)

        request = {'type': 'login'}

        self.proto.write(request)
        response = self.proto.read()

        if response['status'] == 'auth':
            self.auth_mode = response['authentication']
        else:
            raise ConnectionError(response)

    def echo(self):
        while True:
            try:
                response = self.proto.read()
                if response['type'] in self.handlers:
                    self.handlers[response['type']](response)
            except ConnectionError:
                break

    def _send(self, data_json):
        """ Method for handling server responses 'send' type.  """

        print(CLEARING_STRING)
        print(f"{data_json['data']}\n")

    def auth(self, username=None, password=None):
        request = {'type': 'auth'}

        if username:
            request['username'] = username
        if password:
            request['password'] = password

        self.proto.write(request)
        response = self.proto.read()

        if response['status'] == 'ok':
            self.username = response.get('username')
        else:
            raise ConnectionError(response)

    def logout(self):
        request = {'type': 'logout'}
        self.proto.write(request)

        # Wait the server closes the connection itself
        # Connection is broken forced if the server did not time to do
        time.sleep(0.2)
        self.proto.disconnect()

    def send(self, data):
        request = {'type': 'send', 'data': data}
        self.proto.write(request)
