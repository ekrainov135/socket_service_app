import asyncio

from app.protocol import SocketProtocol
from services.common import Service


class ManagerService(Service):
    """ The class of the managing manager-service.
        Has meta-information about other server services and sends it on request.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.services = []

    def run(self, *args, **kwargs):
        self.services = args[0] or kwargs.get('services') or self.services
        self.proto.run_echo_server(self.host, self.port, self.accept_callback)

    def get_services_meta(self):
        services_id = [x.id for x in self.services]
        services_meta = []
        for service in self.services:
            service_data = {}
            service_data['host'] = service.host
            service_data['port'] = service.port
            service_data['service'] = type(service).__name__
            service_data['protocol'] = type(service.proto).__name__
            service_data['args'] = service.proto.args
            service_data['kwargs'] = service.proto.kwargs
            services_meta.append(service_data)

        result = dict(zip(services_id, services_meta))
        return result

    def stop(self):
        self.proto.stop()

    async def accept_callback(self, connection, address):
        try:
            # Sending services metadata
            services_metadata = self.get_services_meta()
            self.proto.write(services_metadata, connection)
            await asyncio.sleep(9999)
        except ConnectionError as e:
            pass
        finally:
            connection.close()
