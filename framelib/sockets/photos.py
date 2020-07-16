import datetime
import tornado.ioloop
import json

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
        self.photo_manager.socket = self.socket
        self.photo_last_update = None
        # super().__init__(*args, **kwargs)
        self.photo_timer = tornado.ioloop.PeriodicCallback(
            self._update_photo,
            callback_time=500
        )

    def open(self):
        pass

    def _update_photo(self):
        if (self.photo_last_update is None
            or
            (datetime.datetime.utcnow() - self.photo_last_update > self.photo_update_interval)
        ):
            print('updating photo')
            if self.photo_manager.auth():
                photoname = self.photo_manager.get_photo()
                print('photoname to send', photoname)
                self.write_message(photoname)
                self.photo_last_update = datetime.datetime.utcnow()

    def write_message(self, message):
        self.socket.write_message('photo', message)

    def callback(self, newstate):
        auth = newstate.get(
            'auth', None
        )
        if auth:
            print('callback auth 2', str(auth))
            if not self.photo_manager.auth(**auth):
                # restart auth process
                print('restarting auth')
                self.photo_manager.auth()
            else:
                self.socket.write_message('auth', 'authorised')

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
