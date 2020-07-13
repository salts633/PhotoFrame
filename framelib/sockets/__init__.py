import tornado.websocket
import json
import collections.abc

from .photos import PhotoHandler
from .settings import SettingsHandler

class MainSocketHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, app_handlers=None, **kwargs):
        self.state = {}
        self.app_handlers = []
        if app_handlers is not None:
            for handler, handlerkwargs in app_handlers:
                self.register_handler(handler(socket=self, **handlerkwargs))
        super().__init__(*args, **kwargs)

    def register_handler(self, handler):
        self.app_handlers.append(handler)

    def on_message(self, json_message):
        newstate = json.loads(json_message)
        self.update_state(newstate)

    def update_state(self, newstate):
        def update(d, u):
            for k, v in u.items():
                if isinstance(v, collections.abc.Mapping):
                    d[k] = update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d
        update(self.state, newstate)
        for handler in self.app_handlers:
            handler.callback(self.state)

    def write_message(self, mtype, message):
        json_message = json.dumps({'type': mtype, 'message': message})
        print('wriitng message', json_message)
        super().write_message(json_message)

    def on_close(self):
        for handler in self.app_handlers:
            handler.close()