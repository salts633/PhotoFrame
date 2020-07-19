import os.path
import pickle
import collections


class SettingsHandler():
    def __init__(self, *args, DEFAULT_CONFIG=None, **kwargs):
        self.config = DEFAULT_CONFIG
        self._pickle_name = self.config['settings']['persist_pickle_path']
        if os.path.exists(self._pickle_name):
            with open(self._pickle_name, 'rb') as f:
                self._persistent_settings = pickle.load(f)
        else:
            self._persistent_settings = {
                'photoUpdateInterval': self.config['settings']['photo_update_interval_seconds'],
                'photoIntervalMode': self.config['settings']['photo_update_mode']
            }
        self._persistent_keys = self._persistent_settings.keys()
        self._appsettings = self._persistent_settings.copy()
        # always start paused to avoid auth issues
        self._appsettings['playPause'] = 'pause'
        self._transient_settings = ['skip']
        self.socket = kwargs.get('socket')

    def _recursive_dict_update(self, d, u):
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = self._recursive_dict_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    @property
    def appsettings(self):
        return self._appsettings

    @property
    def persistent_settings(self):
        return self._persistent_settings

    # no setter for persitent_settings as it should always
    # be set automatically when appsettings is
    @appsettings.setter
    def appsettings(self, newsettings):
        if newsettings != self._appsettings:
            print('new settings found', newsettings)
            self._appsettings = newsettings
            self.write_message(newsettings)

        persist = self._persistent_settings.copy()
        self._recursive_dict_update(
            persist,
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
        settings = newstate.get('settings', {})
        newsettings = self.appsettings.copy()
        self._recursive_dict_update(newsettings, settings)
        self.appsettings = self._remove_transient(newsettings)

    def _remove_transient(self, newsettings):
        filtered = newsettings.copy()
        for s in self._transient_settings:
            filtered.pop(s, None)
        return filtered

    def close(self):
        pass
