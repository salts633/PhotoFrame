import logging
import datetime

import tornado.ioloop

from framelib.Exceptions import PhotoAlbumException

LOG = logging.getLogger("tornado.application.sockets.photos")


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
        self.photo_album = None
        self.photo_history = []
        self.max_history = self.config["photos"]["max_history"]
        self._sendindex = -1  # first retrieval will += 1 this
        self.canforward = None
        self.canbackward = None
        self.photo_last_update = None
        self.photo_timer = tornado.ioloop.PeriodicCallback(
            self._update_photo, callback_time=500
        )
        LOG.info("PhotoHandler initialized with photo_manager: %s", self.photo_manager)

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
        LOG.debug("PhotoSocket opened")

    def _update_photo(self):
        LOG.debug("_update_photo_called")
        if self.photo_last_update is None or (
            datetime.datetime.utcnow() - self.photo_last_update
            > self.photo_update_interval
        ):
            LOG.debug("updating photo")
            if self.photo_manager.auth():
                LOG.debug("photo_manager is authorized")
                try:
                    photoname = self.photo_manager.get_photo()
                    self.photo_history.append(photoname)
                    if len(self.photo_history) > self.max_history:
                        self.photo_history = self.photo_history[1:]
                    else:
                        self.sendindex += 1
                    self.send_photo()
                except PhotoAlbumException:
                    self.socket.update_state("settings", {"photoCurrentAlbum": None})

    def send_photo(self):
        LOG.debug("Photo name to send: %s", self.photo_history[self.sendindex])
        self.write_message(self.photo_history[self.sendindex])
        self.photo_last_update = datetime.datetime.utcnow()

    def write_message(self, message):
        LOG.debug("PhotoSocketHandler sending message %s", message)
        self.socket.write_message("photo", message)

    def callback(self, newstate):
        LOG.debug("PhotoSocketHandler callback")
        auth = newstate.get("auth", None)
        if auth:
            LOG.debug("PhotoSocketHandler 'auth' string found: %s", auth)
            if not self.photo_manager.auth(**auth):
                # restart auth process
                LOG.debug("OAuth step 2 failed, restarting")
                self.photo_manager.auth()
            else:
                LOG.debug("OAuth step 2 succeeded, sending play command")
                self.socket.update_state(
                    {"settings": {"playPause": "play"}, "auth": None}
                )
                self.socket.write_message("auth", "authorised")

        settings = newstate.get("settings", {})
        playpause = settings.get("playPause", "")
        if playpause == "play":
            LOG.debug("found play, starting timer")
            self.photo_timer.start()
        elif playpause == "pause":
            LOG.debug("found pause, stoping timer")
            self.photo_timer.stop()
        else:
            LOG.debug(
                "Unexpected value found for playPause in settings (%s), ignoring",
                playpause,
            )
        skip = settings.get("skip", "")
        if skip == "forward" and self.canforward:
            self.sendindex += 1
            LOG.debug("found skip forward")
            self.send_photo()
        elif skip == "backward" and self.canbackward:
            LOG.debug("found skip backward")
            self.sendindex -= 1
            self.send_photo()
        update_interval = settings.get("photoUpdateInterval", None)
        if update_interval:
            LOG.debug("found new photoUpdateInterval: %s", update_interval)
            self.photo_update_interval = datetime.timedelta(
                seconds=int(update_interval)
            )
        photo_album = settings.get("photoCurrentAlbum", None)
        if photo_album:
            LOG.debug("found new photoCurrentAlbum: %s", photo_album)
            if photo_album != self.photo_album:
                self.photo_album = photo_album
                self.photo_manager.set_album(photo_album)
        if settings.get("refresh_albums", False):
            self.photo_manager.get_album_list()

    def close(self):
        self.photo_timer.stop()
        LOG.debug("photo timer stopped on PhotoSocketHandler close")
