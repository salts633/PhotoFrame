import os.path
import pickle
import collections
from .photos import PHOTO_DEFAULT_UPDATE_INTERVAL


class SettingsHandler():
    def __init__(self, *args, **kwargs):
        if os.path.exists('settings.pickle'):
            self.appsettings = pickle.load('settings.pickle')
        else:
            self.appsettings = {
                'photoUpdateInterval': PHOTO_DEFAULT_UPDATE_INTERVAL
            }
        # always start paused to avoid auth issues
        self.appsettings['playPause'] = 'pause'
        self._transient_settings = ['skip']
        self.socket = kwargs.get('socket')

    def open(self):
        self.write_message(self.appsettings)

    def write_message(self, message):
        self.socket.write_message('settings', message)

    def callback(self, newstate):
        def update(d, u):
            for k, v in u.items():
                if isinstance(v, collections.abc.Mapping):
                    d[k] = update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d
        settings = newstate.get('settings', {})
        newsettings = self.appsettings.copy()
        update(newsettings, settings)
        newsettings = self._remove_transient(newsettings)
        if newsettings != self.appsettings:
            print('new settings found', newsettings)
            self.write_message(newsettings)
            self.appsettings = newsettings

    def _remove_transient(self, newsettings):
        filtered = newsettings.copy()
        for s in self._transient_settings:
            filtered.pop(s, None)
        return filtered

    def close(self):
        pass
