import threading
from http.server import HTTPServer

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
        httpd = HTTPServer(('0.0.0.0', port), SlackRequestHandler)
        httpd.serve_forever()
