import osmapi  # type:ignore
from osmapi import OsmApi
from pydantic import BaseModel
from shapely import Point

import config


class OsmNoteUploader(BaseModel):
    client: OsmApi = OsmApi()
    username: str = config.username
    password: str = config.password
    initialized: bool = False

    class Config:
        arbitrary_types_allowed = True

    def initialize_client(self):
        self.client = OsmApi(self.username, self.password)
        self.initialized = True

    def create_and_upload_note(self, point: Point, text: str = config.note_text) -> int:
        # Create a new note
        latitude = point.y
        longitude = point.x
        try:
            note = self.client.NoteCreate(
                dict(latitude=latitude, longitude=longitude, text=text)
            )
            print(note)
            return note["id"]
        except Exception as e:
            print(f"Error creating note: {str(e)}")
