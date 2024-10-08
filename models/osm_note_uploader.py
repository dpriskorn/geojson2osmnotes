import logging
import os.path
from datetime import datetime

import pandas
from osmapi import OsmApi, ElementDeletedApiError, NoteAlreadyClosedApiError
from pandas import DataFrame
from pydantic import BaseModel, validate_call
from shapely import Point

import config

logger = logging.getLogger(__name__)


class NoneException(BaseException):
    pass


class HiddenNoteError(BaseException):
    pass


class OsmNoteHandler(BaseModel):
    """Class to handle uploading and saving notes to disk"""

    client: OsmApi = OsmApi()
    username: str = config.username
    password: str = config.password
    initialized: bool = False
    notes_file_path: str = ""

    class Config:
        arbitrary_types_allowed = True

    def initialize_client(self):
        # install oauthlib for requests:  pip install requests-oauth2client
        from requests_oauth2client import OAuth2Client, OAuth2AuthorizationCodeAuth
        import requests
        import webbrowser
        import osmapi
        # from dotenv import load_dotenv, find_dotenv
        import os

        # load_dotenv(find_dotenv())

        # Credentials you get from registering a new application
        # register here: https://master.apis.dev.openstreetmap.org/oauth2/applications
        # or on production: https://www.openstreetmap.org/oauth2/applications
        client_id = os.getenv("OSM_OAUTH_CLIENT_ID")
        client_secret = os.getenv("OSM_OAUTH_CLIENT_SECRET")

        # special value for redirect_uri for non-web applications
        redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

        # production
        authorization_base_url = "https://www.openstreetmap.org/oauth2/authorize"
        token_url = "https://www.openstreetmap.org/oauth2/token"

        oauth2client = OAuth2Client(
            token_endpoint=token_url,
            authorization_endpoint=authorization_base_url,
            redirect_uri=redirect_uri,
            auth=(client_id, client_secret),
            code_challenge_method="",
        )

        # open OSM website to authrorize user using the write_api and write_notes scope
        scope = ["write_notes"]
        az_request = oauth2client.authorization_request(scope=scope)
        print(f"Authorize user using this URL: {az_request.uri}")
        webbrowser.open(az_request.uri)

        # create a new requests session using the OAuth authorization
        auth_code = input("Paste the authorization code here: ")
        auth = OAuth2AuthorizationCodeAuth(
            oauth2client,
            auth_code,
            redirect_uri=redirect_uri,
        )
        oauth_session = requests.Session()
        oauth_session.auth = auth

        # use the custom session
        self.client = osmapi.OsmApi(
            # api="https://api06.dev.openstreetmap.org",
            created_by=config.user_agent,
            session=oauth_session)
        logger.info("sucessfully logged into osm using oauth2")
        # with api.Changeset({"comment": "My first test"}) as changeset_id:
        #     print(f"Part of Changeset {changeset_id}")
        #     node1 = api.NodeCreate({"lon": 1, "lat": 1, "tag": {}})
        #     print(node1)

    # def initialize_client(self):
    #     self.client = OsmApi(self.username, self.password, created_by=config.user_agent)
    #     self.initialized = True

    @validate_call(config=dict(arbitrary_types_allowed=True))
    def create_and_upload_note(self, point: Point, text: str = config.note_text) -> int:
        logger.debug("Creating a new note")
        latitude = point.y
        longitude = point.x
        try:
            note = self.client.NoteCreate(dict(lat=latitude, lon=longitude, text=text))
            logger.debug(note)
            # When debugging we show the input
            if config.press_enter_to_continue or config.debug:
                input("Press enter to continue")
            note_id = note["id"]
            if self.is_hidden(note_id=note_id):
                raise HiddenNoteError()
            self.write_note_information_to_csv(note_id=note_id, point=point)
            return note_id
        except Exception as e:
            print(f"Error creating note: {str(e)}")

    @validate_call(config=dict(arbitrary_types_allowed=True))
    def write_note_information_to_csv(self, note_id: int, point: Point) -> None:
        """Store the note information in a csv file"""
        logger.debug("write_note_information_to_csv: running")
        # open the csv with pandas
        file = self.notes_file_path
        if os.path.exists(file) and os.path.getsize(file):
            df = pandas.read_csv(file)
        else:
            df = DataFrame()
        new_data = {
            "date": [datetime.today()],
            "note_id": [note_id],
            "latitude": [point.y],
            "longitude": [point.x],
            "open": True,
            "hidden": False
        }

        # Append the new data to the DataFrame
        df = pandas.concat([df, pandas.DataFrame(new_data)], ignore_index=True)
        # write
        df.to_csv(file, index=False)

    def is_open(self, note_id: int) -> bool:
        try:
            note = self.client.NoteGet(id=note_id)
            # print(note)
            # note_id = note["id"]
            note_status = note["status"]
            status_mapping = {"open": True, "closed": False}
            is_open = status_mapping.get(
                note_status, None
            )  # Returns False for unknown statuses
            if is_open is not None:
                return is_open
            else:
                raise NoneException()
        except ElementDeletedApiError as e:
            # Why does this happen? Because the node has been hidden by a moderator?
            # See https://wiki.openstreetmap.org/wiki/API_v0.6
            # awaiting response from the operations team
            logger.info(f"Error getting note status: {str(e)}")
            # Defaulting to False
            return False

    def is_hidden(self, note_id: int) -> bool:
        try:
            self.client.NoteGet(id=note_id)
            return False
        except ElementDeletedApiError:
            return True

    def close(self, note_id: int, comment) -> bool:
        try:
            self.client.NoteClose(note_id, comment)
            return True
        except NoteAlreadyClosedApiError:
            print(f"{note_id} already closed")
            return True