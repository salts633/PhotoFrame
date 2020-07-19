import os
import pickle
import json
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import google_auth_httplib2  # This gotta be installed for build() to work
import requests
import shutil
import random
import datetime
from pathlib import Path
import urllib.parse as urlparse

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
            return True
        if not self.flow:
            self.flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json",
                SCOPES,
                # redirect_uri= 'http://' + self.socket.request.host + '/auth/google'
                # redirect_uri="urn:ietf:wg:oauth:2.0:oob:auto"
                redirect_uri="http://localhost:8888/auth/",
            )
        PICKLE_PATH = "token.pickle"
        token = kwargs.get("token", None)
        if token:
            print("auth2 query token", token)
            query = urlparse.parse_qs(urlparse.urlparse(token).query)
            if "error" in query or "code" not in query:
                print("auth step 2 failed")
                return False
            # part 2 of authorisation step
            print("auth2 token code", query["code"])
            self.flow.fetch_token(code=query["code"][0])
            self.CREDS = self.flow.credentials
            if not self.CREDS.valid:
                return False
            with open(PICKLE_PATH, "wb") as tokenFile:
                pickle.dump(self.CREDS, tokenFile)
            return True
        # part 1 of authorisation process
        if os.path.exists(PICKLE_PATH):
            with open("token.pickle", "rb") as tokenFile:
                self.CREDS = pickle.load(tokenFile)
        if not self.CREDS or not self.CREDS.valid:
            if self.CREDS and self.CREDS.expired and self.CREDS.refresh_token:
                self.CREDS.refresh(Request())
            else:
                print("flow from secrets file")
                auth_url = self.flow.authorization_url()[0]
                self.socket.write_message("auth_redirect", auth_url)
                return False
        if not self.service:
            print("building service")
            self.service = build(
                "photoslibrary", "v1", credentials=self.CREDS, cache_discovery=False
            )
        return True

    def get_album(self, album_name):
        page_token = True
        while page_token:
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
        if not self.album_id:
            self.get_album(self.album_name)
        if self.photos_last_updated:
            update_interval = datetime.datetime.utcnow() - self.photos_last_updated

        if (
            self.photos is None
            or self.photos_last_updated is None
            or update_interval > self.photo_update_interval
        ):
            print("updating photo in album list")
            self.photos = []
            page_token = True
            while page_token:
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
            photo = self.photo_cache[fetch_id]
        else:
            print("fetching single photo metadata")
            photo = self.service.mediaItems().get(mediaItemId=fetch_id).execute()
            # TODO the docs say not to use baseUrl raw, check them
            r = requests.get(photo["baseUrl"])
            if r.status_code == 200:
                saveto = self.photos_path / Path(photo["filename"])
                if not os.path.exists(saveto):
                    with open(saveto, "wb") as f:
                        for chunk in r:
                            f.write(chunk)
            # print(photo)
            self.photo_cache[fetch_id] = photo

        return photo["filename"]


if __name__ == "__main__":
    print("testing google photos")
    man = Manager()
    print(man.get_photo())
