import threading

import tornado.ioloop
import tornado.web

from lib import SqdcStore
from lib.SlackRequestHandler import SlackRequestHandler


class SlackEndpointServer:

    def __init__(self, port, watcher, store):
        threading.Thread(target=self.listen_server, args=[port, watcher, store]).start()

    @staticmethod
    def listen_server(port, watcher, store: SqdcStore):
        SlackRequestHandler.watcher = watcher
        SlackRequestHandler.store = store
        server = tornado.web.Application([
            (r"/", SlackRequestHandler)
        ])

        ioloop = tornado.ioloop.IOLoop()
        ioloop.make_current()

        server.listen(port)
        ioloop.start()
