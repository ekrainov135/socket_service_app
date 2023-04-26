from abc import abstractmethod, ABC
import asyncio


class Service(ABC):

    WORK_DIR = ''

    def __init__(self, service_id, proto, host=None, port=None, **kwargs):
        self.id = service_id
        self.loop = asyncio.get_event_loop()
        self.proto = proto
        self.host = host
        self.port = port
        self.is_active = False
        #self.enable_address = enable_address
        #self.authenticator = authenticator

    def run(self, *args, **kwargs):
        self.proto.run_echo_server(self.host, self.port, self.accept_callback)
        self.is_active = True

    async def accept_callback(self, connection, address):
        pass

    def stop(self):
        self.proto.stop()
        self.is_active = False
