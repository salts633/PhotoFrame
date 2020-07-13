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

SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']

class GooglePhotosException(Exception):
    """Base class for exceptions concerning Google Photos"""

class AlbumException(GooglePhotosException):
    """Exception relating to Google Photos Album"""

class PhotoListException(GooglePhotosException):
    """Exception fetching Google Photos"""

class Manager():
    CREDS = None
    
    def __init__(self, photos_path='photos', album_name='Frame',
                 photo_update_interval=datetime.timedelta(hours=6)):
        self.photos_path = photos_path
        self.album_name = album_name
        self.photo_update_interval = photo_update_interval
        if(os.path.exists("token.pickle")):
            with open("token.pickle", "rb") as tokenFile:
                self.CREDS = pickle.load(tokenFile)
        if not self.CREDS or not self.CREDS.valid:
            if (self.CREDS and self.CREDS.expired and self.CREDS.refresh_token):
                self.CREDS.refresh(Request())
            else:
                print('flow from secrets file')
                flow = InstalledAppFlow.from_client_secrets_file('../client_secret.json', SCOPES)
                self.CREDS = flow.run_local_server(port = 0)
            with open("token.pickle", "wb") as tokenFile:
                pickle.dump(self.CREDS, tokenFile)
        print('building service')
        self.service = build('photoslibrary', 'v1', credentials = self.CREDS, cache_discovery=False)
        self.album_id = None
        self.photos = None
        self.photos_last_updated = None
        self.photo_cache = {}

    def get_album(self, album_name):
        page_token = True
        while page_token:
            if page_token is True:
                page_token = None
            results = self.service.albums().list(
                pageSize=50,
                pageToken=page_token,
                fields="nextPageToken,albums(id,title)"
            ).execute()
            albums = results.get('albums', [])
            self.album_id = None
            for album in albums:
                if album['title'] == album_name:
                    self.album_id = album['id']
                    break
            if self.album_id:
                break
            page_token = results.get('nextPageToken', None)
        else:
            raise GooglePhotosException(
                f"Unable to find requested album"
            )

    def get_photo(self):
        if not self.album_id:
            self.get_album(self.album_name)
        if self.photos_last_updated:
            update_interval = datetime.datetime.utcnow() - self.photos_last_updated

        if (self.photos is None or
            self.photos_last_updated is None or
            update_interval > self.photo_update_interval
        ):
            print('updating photo in album list')
            self.photos = []
            page_token = True
            while page_token:
                if page_token is True:
                    page_token = None
                request = (
                    self.service.mediaItems().search(
                        body={
                            'pageToken': page_token,
                            'albumId': self.album_id
                        }
                    ).execute()
                )
                page_token = request.get('nextPageToken', None)
                self.photos += request.get('mediaItems', [])
            if self.photos:
                self.photos_last_updated = datetime.datetime.utcnow()
            else:
                self.photos = None
                raise PhotoListException("No photos in album")

        fetch_id = random.choice(self.photos)['id']

        if fetch_id in self.photo_cache:
            photo = self.photo_cache[fetch_id]
        else:
            print('fetching single photo metadata')
            photo = (
                self.service.mediaItems(
                ).get(
                    mediaItemId=fetch_id
                ).execute()
            )
            # TODO the docs say not to use baseUrl raw, check them
            r = requests.get(photo['baseUrl'])
            if r.status_code == 200:
                saveto = self.photos_path / Path(photo['filename'])
                if not os.path.exists(saveto):
                    with open(saveto, 'wb') as f:
                        for chunk in r:
                            f.write(chunk)
            # print(photo)
            self.photo_cache[fetch_id] = photo

        return(photo['filename'])


if __name__ == "__main__":
    print('testing google photos')
    man = Manager()
    print(man.get_photo())
