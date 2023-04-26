import asyncio
from functools import partial
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


DEFAULT_SERVICE_EXECUTOR = ThreadPoolExecutor


class Server:
    """ The main interface for interacting with services. Gets service objects and runs them asynchronously
        in separate executors.
    """

    def __init__(self, services=None, executors=None, **kwargs):
        self.services = services or []
        self.executors = executors or dict([(service.id, DEFAULT_SERVICE_EXECUTOR()) for service in self.services])
        self.params = kwargs
        self.loop = asyncio.get_event_loop()

    def run(self):
        tasks = []
        try:
            for service in self.services:
                params = self.params.get('_{}'.format(service.id))
                params = tuple(params) if params else ()
                if type(service).__name__ == 'ManagerService':
                    params = (self.services, *params)
                run_task = partial(service.run, *params)
                tasks.append(self.loop.run_in_executor(None, run_task))
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    def abort(self):
        pass
