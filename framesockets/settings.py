import tornado.websocket

from .photos import PHOTO_DEFAULT_UPDATE_INTERVAL


class SettingsHandler():
    def __init__(self, *args, **kwargs):
        self.appsettings = {
            'playPause': 'play',
            'photoUpdateInterval': PHOTO_DEFAULT_UPDATE_INTERVAL
        }
        self.socket = kwargs.pop('socket')
        # super().__init__(*args, **kwargs)

    def callback(self, newstate):
        print('settings socket recived message', newstate)
        pass
    #    self.raw_socket.write_message('settings', u"You said: " + message)

    def close(self):
        pass
