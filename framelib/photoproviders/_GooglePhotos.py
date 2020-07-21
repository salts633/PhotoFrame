import os
import logging
import datetime
import pickle
import random
import urllib.parse as urlparse
from pathlib import Path

import requests
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

LOG = logging.getLogger("tornado.application.photoproviders.Google")

SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]


class GooglePhotosException(Exception):
    """Base class for exceptions concerning Google Photos"""


class AlbumException(GooglePhotosException):
    """Exception relating to Google Photos Album"""


class PhotoListException(GooglePhotosException):
    """Exception fetching Google Photos"""


class Manager:
    CREDS = None

    def __init__(self, DEFAULT_CONFIG=None):
        self.config = DEFAULT_CONFIG
        self.photos_path = self.config["photos"]["Google"]["STORE_PATH"]
        self.album_name = self.config["photos"]["Google"]["album"]
        self.photo_update_interval = datetime.timedelta(
            seconds=self.config["settings"]["photo_update_interval_seconds"]
        )
        self.flow = None
        self.CREDS = None
        self.service = None

        self.socket = None
        self.album_id = None
        self.photos = None
        self.last_photo = ""
        self.photos_last_updated = None
        self.photo_cache = {}

    def auth(self, **kwargs):
        if self.service:
            LOG.debug("Existing Google service, authorization not required.")
            return True
        if not self.flow:
            LOG.info("Starting new authorisation flow")
            self.flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json",
                SCOPES,
                redirect_uri="http://localhost:8888/auth/",
            )
        PICKLE_PATH = "token.pickle"
        token = kwargs.get("token", None)
        if token:
            LOG.debug("Google OAuth step 2 using token %s", token)
            query = urlparse.parse_qs(urlparse.urlparse(token).query)
            if "error" in query or "code" not in query:
                LOG.error("Google OAuth step 2 error")
                return False
            # part 2 of authorisation step
            LOG.debug("Google OAuth auth token code: %s", query["code"])
            self.flow.fetch_token(code=query["code"][0])
            self.CREDS = self.flow.credentials
            if not self.CREDS.valid:
                return False
            with open(PICKLE_PATH, "wb") as tokenFile:
                LOG.info("Writing Google credentials to %s ", PICKLE_PATH)
                pickle.dump(self.CREDS, tokenFile)
                tokenFile.flush()
                os.fsync(tokenFile.fileno())
            return True
        # part 1 of authorisation process
        if os.path.exists(PICKLE_PATH):
            LOG.debug("Existing Google credentials file exists %s", PICKLE_PATH)
            try:
                with open("token.pickle", "rb") as tokenFile:
                    LOG.info("Reading Google credentials from %s ", PICKLE_PATH)
                    self.CREDS = pickle.load(tokenFile)
            except Exception as exp:
                LOG.error("Loading pickled credentials failed with error %s", exp)
        if not self.CREDS or not self.CREDS.valid:
            LOG.debug("New Google credentials required")
            if self.CREDS and self.CREDS.expired and self.CREDS.refresh_token:
                LOG.info("refreshing Google credentials")
                self.CREDS.refresh(Request())
            else:
                LOG.info("Fetching Google authorization URL")
                auth_url = self.flow.authorization_url()[0]
                self.socket.write_message("auth_redirect", auth_url)
                return False
        if not self.service:
            LOG.info("Authoriztion complete, building seervice.")
            self.service = build(
                "photoslibrary", "v1", credentials=self.CREDS, cache_discovery=False
            )
        return True

    def get_album(self, album_name):
        LOG.debug("Feching album: %s", album_name)
        page_token = True
        while page_token:
            LOG.debug("Fetching albums page")
            if page_token is True:
                page_token = None
            results = (
                self.service.albums()
                .list(
                    pageSize=50,
                    pageToken=page_token,
                    fields="nextPageToken,albums(id,title)",
                )
                .execute()
            )
            albums = results.get("albums", [])
            self.album_id = None
            for album in albums:
                if album["title"] == album_name:
                    self.album_id = album["id"]
                    break
            if self.album_id:
                break
            page_token = results.get("nextPageToken", None)
        else:
            raise GooglePhotosException(f"Unable to find requested album")

    def get_photo(self):
        LOG.debug("get_photo called")
        if not self.album_id:
            self.get_album(self.album_name)
        if self.photos_last_updated:
            update_interval = datetime.datetime.utcnow() - self.photos_last_updated

        if (
            self.photos is None
            or self.photos_last_updated is None
            or update_interval > self.photo_update_interval
        ):
            LOG.debug("Updating photos in album list")
            self.photos = []
            page_token = True
            while page_token:
                LOG.debug("Fetching photos page")
                if page_token is True:
                    page_token = None
                request = (
                    self.service.mediaItems()
                    .search(body={"pageToken": page_token, "albumId": self.album_id})
                    .execute()
                )
                page_token = request.get("nextPageToken", None)
                self.photos += request.get("mediaItems", [])
            if self.photos:
                self.photos_last_updated = datetime.datetime.utcnow()
            else:
                self.photos = None
                raise PhotoListException("No photos in album")

        fetch_id = random.choice(self.photos)["id"]
        if len(self.photos) > 1:
            while fetch_id == self.last_photo:
                # ensure we don't return the same photo twice in a row
                fetch_id = random.choice(self.photos)["id"]
        self.last_photo = fetch_id

        if fetch_id in self.photo_cache:
            LOG.debug("getting photo from cache")
            photo = self.photo_cache[fetch_id]
        else:
            LOG.debug("Getting new photo metadata")
            photo = self.service.mediaItems().get(mediaItemId=fetch_id).execute()
            # TODO the docs say not to use baseUrl raw, check them
            r = requests.get(photo["baseUrl"])
            if r.status_code == 200:
                saveto = self.photos_path / Path(photo["filename"])
                if not os.path.exists(saveto):
                    with open(saveto, "wb") as f:
                        for chunk in r:
                            f.write(chunk)
            self.photo_cache[fetch_id] = photo
        LOG.debug("Found photo %s", photo)
        return photo["filename"]


if __name__ == "__main__":
    print("testing google photos")
    man = Manager()
    print(man.get_photo())
