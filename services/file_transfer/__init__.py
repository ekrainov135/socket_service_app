import asyncio

from services.common import Service


class FileTransferService(Service):
    async def accept_callback(self, connection, address):
        try:
            # Sending services metadata
            self.proto.write('ok', connection)
            await asyncio.sleep(9999)
        except ConnectionError as e:
            pass
        finally:
            connection.close()
