import tornado.escape
import tornado.ioloop
import tornado.locks
import tornado.web
import tornado.websocket
import os.path
import datetime
import json

from photoproviders import GooglePhotos
from framesockets import MainSocketHandler
from framesockets.photos import PhotoHandler
from framesockets.settings import SettingsHandler

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=True, help="run in debug mode")

PHOTOS_PATH='photos'

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(
            "index.html",
            SERVER_ADDRESS=self.request.host,
            PHOTOS_PATH=PHOTOS_PATH
        )


def main():
    parse_command_line()
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/socket", MainSocketHandler,
             {'app_handlers': [
                    (PhotoHandler, {'photo_manager': GooglePhotos()}),
                    (SettingsHandler, {}),
                ]
             }
            ),
            (r"/" + PHOTOS_PATH + '/(.*)', tornado.web.StaticFileHandler, {'path': PHOTOS_PATH})
        ],
        autoreload=True, # TODO dev option
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
    )
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
