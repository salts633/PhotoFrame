import datetime
import tornado.ioloop

PHOTO_DEFAULT_UPDATE_INTERVAL = 5 # in integer seconds

class PhotoHandler():

    def __init__(self, *args, **kwargs):
        self.photo_update_interval = datetime.timedelta(
            seconds=kwargs.pop(
                'photo_update_interval', PHOTO_DEFAULT_UPDATE_INTERVAL
            )
        )
        self.socket = kwargs.get('socket')
        self.photo_manager = kwargs.pop('photo_manager')
        self.photo_last_update = None
        # super().__init__(*args, **kwargs)
        self.photo_timer = tornado.ioloop.PeriodicCallback(
            self._update_photo,
            callback_time=500
        )

    def open(self):
        self.photo_timer.start()

    def _update_photo(self):
        if (self.photo_last_update is None
            or
            (datetime.datetime.utcnow() - self.photo_last_update > self.photo_update_interval)
        ):
            print('updating photo')
            photoname = self.photo_manager.get_photo()
            print('photoname to send', photoname)
            self.write_message(photoname)
            self.photo_last_update = datetime.datetime.utcnow()

    def write_message(self, message):
        self.socket.write_message('photo', message)

    def callback(self, newstate):
        playpause = newstate.get(
            'settings', {}
        ).get('playPause', '')
        if playpause == 'play':
            print('callback starting timer')
            self.photo_timer.start()
        elif playpause == 'pause':
            print('callback stoping timer')
            self.photo_timer.stop()
        else:
            pass
            #TODO log unexpected input

    def close(self):
        self.photo_timer.stop()
        print("photo timer stopped")
