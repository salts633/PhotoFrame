import datetime

import tornado.ioloop


class PhotoHandler:
    def __init__(self, *args, DEFAULT_CONFIG=None, **kwargs):
        self.config = DEFAULT_CONFIG
        self.photo_update_interval = datetime.timedelta(
            seconds=kwargs.pop(
                "photo_update_interval",
                self.config["settings"]["photo_update_interval_seconds"],
            )
        )
        self.socket = kwargs.get("socket")
        self.photo_manager = kwargs.pop("photo_manager")
        self.photo_manager.socket = self.socket
        self.photo_history = []
        self.max_history = self.config["photos"]["max_history"]
        self._sendindex = -1  # first retrieval will += 1 this
        self.canforward = None
        self.canbackward = None
        self.photo_last_update = None
        self.photo_timer = tornado.ioloop.PeriodicCallback(
            self._update_photo, callback_time=500
        )

    @property
    def sendindex(self):
        return self._sendindex

    @sendindex.setter
    def sendindex(self, newindex):
        self._sendindex = newindex
        self.canforward = (
            self.photo_history and self.sendindex < len(self.photo_history) - 1
        )
        self.canbackward = self.photo_history and self.sendindex > 0
        self.socket.update_state(
            {
                "settings": {
                    "canForward": self.canforward,
                    "canBackward": self.canbackward,
                }
            }
        )

    def open(self):
        pass

    def _update_photo(self):
        if self.photo_last_update is None or (
            datetime.datetime.utcnow() - self.photo_last_update
            > self.photo_update_interval
        ):
            print("updating photo")
            if self.photo_manager.auth():
                photoname = self.photo_manager.get_photo()
                self.photo_history.append(photoname)
                if len(self.photo_history) > self.max_history:
                    self.photo_history = self.photo_history[1:]
                else:
                    self.sendindex += 1
                self.send_photo()

    def send_photo(self):
        print("photoname to send", self.photo_history[self.sendindex])
        self.write_message(self.photo_history[self.sendindex])
        self.photo_last_update = datetime.datetime.utcnow()

    def write_message(self, message):
        self.socket.write_message("photo", message)

    def callback(self, newstate):
        auth = newstate.get("auth", None)
        if auth:
            print("callback auth 2", str(auth))
            if not self.photo_manager.auth(**auth):
                # restart auth process
                print("restarting auth")
                self.photo_manager.auth()
            else:
                self.socket.update_state(
                    {"settings": {"playPause": "play"}, "auth": None}
                )
                self.socket.write_message("auth", "authorised")

        settings = newstate.get("settings", {})
        playpause = settings.get("playPause", "")
        if playpause == "play":
            print("callback starting timer")
            self.photo_timer.start()
        elif playpause == "pause":
            print("callback stoping timer")
            self.photo_timer.stop()
        else:
            pass
            # TODO log unexpected input
        skip = settings.get("skip", "")
        if skip == "forward" and self.canforward:
            self.sendindex += 1
            print("skip forward")
            self.send_photo()
        elif skip == "backward" and self.canbackward:
            print("skip backward")
            self.sendindex -= 1
            self.send_photo()
        update_interval = settings.get("photoUpdateInterval", None)
        if update_interval:
            self.photo_update_interval = datetime.timedelta(
                seconds=int(update_interval)
            )

    def close(self):
        self.photo_timer.stop()
        print("photo timer stopped")
