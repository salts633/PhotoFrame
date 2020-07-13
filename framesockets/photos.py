import datetime

import tornado.ioloop

PHOTO_DEFAULT_UPDATE_INTERVAL = datetime.timedelta(seconds=5)

class PhotoHandler():

    def __init__(self, *args, **kwargs):
        self.photo_update_interval = kwargs.pop(
            'photo_update_interval', PHOTO_DEFAULT_UPDATE_INTERVAL
        )
        self.socket = kwargs.pop('socket')
        self.photo_manager = kwargs.pop('photo_manager')
        self.photo_last_update = None
        # super().__init__(*args, **kwargs)
        self.photo_timer = tornado.ioloop.PeriodicCallback(
            self._update_photo,
            callback_time=500
        )
        self.photo_timer.start()

    def _update_photo(self):
        if (self.photo_last_update is None
            or
            (datetime.datetime.utcnow() - self.photo_last_update > self.photo_update_interval)
        ):
            print('updating photo')
            photoname = self.photo_manager.get_photo()
            print('photoname to send', photoname)
            self.socket.write_message('photo', photoname)
            self.photo_last_update = datetime.datetime.utcnow()

    def callback(self, newstate):
        pass

    def close(self):
        self.photo_timer.stop()
        print("photo timer stopped")
