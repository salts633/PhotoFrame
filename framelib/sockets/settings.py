
from .photos import PHOTO_DEFAULT_UPDATE_INTERVAL


class SettingsHandler():
    def __init__(self, *args, **kwargs):
        self.appsettings = {
            'playPause': 'play',
            'photoUpdateInterval': PHOTO_DEFAULT_UPDATE_INTERVAL
        }
        self.socket = kwargs.get('socket')

    def open(self):
        self.write_message(self.appsettings)

    def write_message(self, message):
        self.socket.write_message('settings', message)

    def callback(self, newstate):
        newsettings = newstate.get('settings', {})
        self.appsettings.update(newsettings)

    def close(self):
        pass
