import logging
import json

import tornado.websocket

from .photos import PhotoHandler
from .settings import SettingsHandler

LOG = logging.getLogger("tornado.application.sockets")


class MainSocketHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, app_handlers=None, DEFAULT_CONFIG=None, **kwargs):
        # call __init__ at start as some handlers (may) expect
        # a socket to be available when they are initialised
        super().__init__(*args, **kwargs)
        self.config = DEFAULT_CONFIG
        self.app_handlers = []
        if app_handlers is not None:
            for handler, handlerkwargs in app_handlers:
                self.register_handler(handler(socket=self, **handlerkwargs))
        LOG.info("MainSocketHandler initialized")
        LOG.debug("registered app-handlers: %s", self.app_handlers)

    def register_handler(self, handler):
        self.app_handlers.append(handler)

    def open(self, *args, **kwargs):
        super().open(*args, **kwargs)
        LOG.debug("MainSocketHandler opening app_handlers")
        for handler in self.app_handlers:
            handler.open()

    def on_message(self, json_message):
        LOG.info("MainSocketHandler received message:  %s", json_message)
        newstate = json.loads(json_message)
        self.update_state(newstate)

    def update_state(self, newstate):
        LOG.debug("MainSocketHandler updating state with:  %s", newstate)
        for handler in self.app_handlers:
            handler.callback(newstate)

    def write_message(self, mtype, message):
        json_message = json.dumps({"type": mtype, "message": message})
        LOG.debug("MainSocketHandler sending message:  %s", json_message)
        super().write_message(json_message)

    def on_close(self):
        LOG.debug("MainSocketHandler closing app_handlers")
        for handler in self.app_handlers:
            handler.close()
