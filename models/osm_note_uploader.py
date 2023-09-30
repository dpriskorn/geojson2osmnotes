import logging
import os.path
from datetime import datetime

import pandas
from osmapi import OsmApi
from pandas import DataFrame
from pydantic import BaseModel, validate_call
from shapely import Point

import config

logger = logging.getLogger(__name__)


class NoneException(BaseException):
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
        self.client = OsmApi(self.username, self.password)
        self.initialized = True

    @validate_call(config=dict(arbitrary_types_allowed=True))
    def create_and_upload_note(self, point: Point, text: str = config.note_text) -> int:
        # Create a new note
        latitude = point.y
        longitude = point.x
        try:
            note = self.client.NoteCreate(dict(lat=latitude, lon=longitude, text=text))
            # print(note)
            note_id = note["id"]
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
        }

        # Append the new data to the DataFrame
        df = pandas.concat([df, pandas.DataFrame(new_data)], ignore_index=True)
        # write
        df.to_csv(file, index=False)

    def lookup_note_status(self, note_id: int) -> bool:
        try:
            note = self.client.NoteGet(id=note_id)
            # print(note)
            # note_id = note["id"]
            note_status = note["status"]
            # Alternatively, you can use a dictionary to map values to booleans
            status_mapping = {"open": True, "closed": False}
            is_open = status_mapping.get(
                note_status, None
            )  # Returns None for unknown statuses
            if is_open is not None:
                return is_open
            else:
                raise NoneException()
        except Exception as e:
            print(f"Error getting note status: {str(e)}")
