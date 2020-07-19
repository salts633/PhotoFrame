import tornado.websocket
import json
import collections.abc

from .photos import PhotoHandler
from .settings import SettingsHandler


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

    def register_handler(self, handler):
        self.app_handlers.append(handler)

    def open(self, *args, **kwargs):
        super().open(*args, **kwargs)
        for handler in self.app_handlers:
            handler.open()

    def on_message(self, json_message):
        print('recieved message', json_message)
        newstate = json.loads(json_message)
        self.update_state(newstate)

    def update_state(self, newstate):
        for handler in self.app_handlers:
            handler.callback(newstate)

    def write_message(self, mtype, message):
        json_message = json.dumps({'type': mtype, 'message': message})
        print('wriitng message', json_message)
        super().write_message(json_message)

    def on_close(self):
        for handler in self.app_handlers:
            handler.close()