from unittest import TestCase

import pandas
from shapely import Point

import config
from models.osm_note_uploader import OsmNoteHandler


class TestOsmNoteHandler(TestCase):
    def test_lookup_note_status(self):
        osm = OsmNoteHandler()
        # osm.initialize_client()
        # is_open =
        assert osm.lookup_note_status(note_id=3915359) is True

    def test_write_note_information_to_csv(self):
        osm = OsmNoteHandler()
        # osm.initialize_client()
        osm.write_note_information_to_csv(note_id=3915359, point=Point([1, 1]))
        # assert False
        file = config.notes_file
        df = pandas.read_csv(file)
        print(df.info())

    def test_write_note_information_to_csv_invalid(self):
        osm = OsmNoteHandler()
        # osm.initialize_client()
        osm.write_note_information_to_csv(note_id=0, point=Point([1, 1]))
        # assert False
        file = config.notes_file
        df = pandas.read_csv(file)
        print(df.info())
