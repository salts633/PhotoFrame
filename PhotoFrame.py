import logging
import os.path
from pathlib import Path
from importlib import import_module

import configobj
from validate import Validator

import tornado.escape
import tornado.ioloop
import tornado.locks
import tornado.web
import tornado.websocket
from tornado.options import define, options, parse_command_line

import framelib
from framelib.photoproviders import GooglePhotos
from framelib.sockets import MainSocketHandler, PhotoHandler, SettingsHandler

LOG = logging.getLogger("tornado.application")

LOG.info("Starting Up")

config = configobj.ConfigObj(
    "photoframe_defaults.conf",
    configspec=str(
        Path(framelib.__file__).parent / Path("photoframe_defaults_validate.conf")
    ),
)
val = Validator()
config.validate(val)
LOG.debug("Successfully loaded and validated config.")

cacher_name = config["file cache"]["use"]
cacher_settings = config["file cache"][cacher_name]
Cacher = getattr(import_module("diskcacher"), cacher_name)


define(
    "port",
    default=config["server"]["default_port"],
    help="run on the given port",
    type=int,
)


class MainHandler(tornado.web.RequestHandler):
    def __init__(self, *args, DEFAULT_CONFIG=None, **kwargs):
        super().__init__(*args, **kwargs)

    def get(self):
        self.render(
            "index.html",
            SERVER_ADDRESS=self.request.host,
            PHOTOS_PATH=config["photos"]["STORE_PATH"],
        )


def main():
    parse_command_line()
    LOG.debug("tornado command line parsed")

    app = tornado.web.Application(
        [
            (r"/", MainHandler, {"DEFAULT_CONFIG": config}),
            (r"/auth/.*", MainHandler, {"DEFAULT_CONFIG": config}),
            (
                r"/socket",
                MainSocketHandler,
                {
                    "DEFAULT_CONFIG": config,
                    "app_handlers": [
                        (
                            PhotoHandler,
                            {
                                "DEFAULT_CONFIG": config,
                                "photo_manager": GooglePhotos(
                                    DEFAULT_CONFIG=config,
                                    FILE_CACHER=Cacher(
                                        config["photos"]["Google"]["STORE_PATH"],
                                        **cacher_settings
                                    ),
                                ),
                            },
                        ),
                        (SettingsHandler, {"DEFAULT_CONFIG": config}),
                    ],
                },
            ),
            (
                r"/" + config["photos"]["STORE_PATH"] + "/(.*)",
                tornado.web.StaticFileHandler,
                {"path": config["photos"]["STORE_PATH"]},
            ),
        ],
        autoreload=True,  # TODO dev option
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
    )
    LOG.debug("starting listen...")
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
