import os.path
import pickle
import collections
from .photos import PHOTO_DEFAULT_UPDATE_INTERVAL


class SettingsHandler():
    def __init__(self, *args, **kwargs):
        self._pickle_name = 'settings.pickle'
        if os.path.exists(self._pickle_name):
            with open(self._pickle_name, 'rb') as f:
                self._persistent_settings = pickle.load(f)
        else:
            self._persistent_settings = {
                'photoUpdateInterval': PHOTO_DEFAULT_UPDATE_INTERVAL
            }
        self._persistent_keys = self._persistent_settings.keys()
        self.appsettings = self._persistent_settings.copy()
        # always start paused to avoid auth issues
        self.appsettings['playPause'] = 'pause'
        self._transient_settings = ['skip']
        self.socket = kwargs.get('socket')

    @property
    def persistent_settings(self):
        return self._persistent_settings

    @persistent_settings.setter
    def persistent_settings(self, newsettings):
        persist = self._persistent_settings.copy()
        persist.update(
            {
                k: v for k, v in newsettings.items()
                if k in self._persistent_keys
            }
        )
        if self._persistent_settings != persist:
            self._persistent_settings = persist
            with open(self._pickle_name, 'wb') as f:
                pickle.dump(self._persistent_settings, f)

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
