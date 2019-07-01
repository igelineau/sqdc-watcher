import threading

import tornado
from tornado.ioloop import IOLoop

from lib import SqdcStore
from lib.SlackRequestHandler import SlackRequestHandler


class SlackEndpointServer:
    ioloop: IOLoop

    def __init__(self, port, watcher, store):
        threading.Thread(target=self.listen_server, args=[port, watcher, store]).start()

    def listen_server(self, port, watcher, store: SqdcStore):
        SlackRequestHandler.watcher = watcher
        SlackRequestHandler.store = store
        server = tornado.web.Application([
            (r"/", SlackRequestHandler)
        ])

        self.ioloop = IOLoop()
        self.ioloop.make_current()

        server.listen(port)
        self.ioloop.start()

    def stop(self):
        self.ioloop.add_callback_from_signal(self._stop)

    def _stop(self):
        print('Slack Command Server - Shutting down...')
        self.ioloop.stop()
