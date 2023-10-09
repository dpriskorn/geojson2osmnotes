import logging
import os
from argparse import ArgumentParser

import geopandas
import pandas
from geopy.distance import distance
from pandas import DataFrame
from pydantic import BaseModel
from shapely import Point

import config
from models.bounding_box import BoundingBox
from models.exceptions import GeometryError
from models.osm_note_uploader import OsmNoteHandler


logger = logging.getLogger(__name__)


class GeojsonHandler(BaseModel):
    """This class takes care of setting up the
    # get source geojson and osmfeatures geojson from the command line
    # parse with geopandas
    # for every source feature:
      check if it already exists in osm within 100m

    It uses Points defined like this:
    # This is a point object where y=latitude and x=longitude
    latitude = point.y
    longitude = point.x

    """

    source_geojson: str = ""
    osm_geojson: str = ""
    notes_file_path: str = ""
    bounding_box_string: str = ""
    bbox: BoundingBox = BoundingBox()

    source_df: DataFrame = DataFrame()
    osm_df: DataFrame = DataFrame()
    notes_df: DataFrame = DataFrame()

    osmnoteuploader: OsmNoteHandler = OsmNoteHandler()
    number_of_open_notes: int = 0

    class Config:
        arbitrary_types_allowed = True

    def start(self):
        self.setup_argparse_and_get_filename()
        self.parse_bounding_box()
        self.create_geodataframes()
        self.check_number_of_open_notes()
        self.iterate_source_features()

    def parse_bounding_box(self):
        """Parse the format from http://osm.duschmarke.de/bbox.html"""
        if self.bounding_box_string:
            bbox_list = self.bounding_box_string.split(",") #x1,y1,x2,y2
            if not len(bbox_list) == 4:
                raise GeometryError(f"Not a correct bounding box with x1,y1,x2,y2: {self.bounding_box_string}")
            self.bbox = BoundingBox(x1=bbox_list[0],
                                    y1=bbox_list[1],
                                    x2=bbox_list[2],
                                    y2=bbox_list[3])

    def read_notes_dataframe(self):
        if self.notes_df.empty:
            # read the csv if any
            file = self.notes_file_path
            if os.path.exists(file) and os.path.getsize(file):
                self.notes_df = pandas.read_csv(file)

    def check_number_of_open_notes(self):
        self.read_notes_dataframe()
        if not self.notes_df.empty:
            # output number of open notes in cache
            # Count the number of rows where 'open' is True
            count_open_notes_before_check = self.notes_df["open"].sum()
            print(f"Open notes before check: {count_open_notes_before_check}")
            # We dont need to login to get the status only
            # self.initialize_note_uploader()
            # for each note lookup if open
            # Use apply() to update the 'open' column based on the lookup method
            self.notes_df["open"] = self.notes_df["note_id"].apply(
                lambda x: self.osmnoteuploader.lookup_note_status(note_id=x)
            )
            # write back the file
            self.notes_df.to_csv(self.notes_file_path)
            # store number of open notes in an attibute
            count_open_notes_after_check = self.notes_df["open"].sum()
            print(f"Open notes after check: {count_open_notes_after_check}")
            self.number_of_open_notes = count_open_notes_after_check
        else:
            print(f"Open notes: {self.number_of_open_notes}")

    def create_geodataframes(self):
        """Create geodataframes based on the geojson input files"""
        self.source_df = geopandas.read_file(self.source_geojson)
        if config.loglevel == logging.INFO:
            print(self.source_df.info())
        self.osm_df = geopandas.read_file(self.osm_geojson)

    @staticmethod
    def calculate_distance_geopandas(row, target_point):
        # This is a Shapely point object where y=latitude and x=longitude
        # see https://stackoverflow.com/questions/49635436/shapely-point-geometry-in-geopandas-df-to-lat-lon-columns
        # invocation Point([y, x])
        if row.geometry.geom_type == "Point":
            row_coords = (row.geometry.y, row.geometry.x)
        elif row.geometry.geom_type == "Polygon":
            row_coords = (row.geometry.centroid.y, row.geometry.centroid.x)
        elif row.geometry.geom_type == "LineString":
            closest_point = row.geometry.interpolate(row.geometry.project(target_point))
            row_coords = (closest_point.y, closest_point.x)
        else:
            raise GeometryError(f"row.geometry.type: {row.geometry.type} not supported")
        dist = distance(row_coords, (target_point.y, target_point.x)).meters
        return dist

    @staticmethod
    def generate_osm_url(point):
        """
        Generates an OpenStreetMap URL for a given Shapely Point.

        Args:
            point (shapely.geometry.point.Point): A Shapely Point object.

        Returns:
            str: The OpenStreetMap URL in the format https://www.openstreetmap.org/#map=19/{latitude}/{longitude}
        """
        # This is a point object where y=latitude and x=longitude
        latitude = point.y
        longitude = point.x
        return f"https://www.openstreetmap.org/#map=19/{latitude}/{longitude}"

    def initialize_note_uploader(self):
        if not self.osmnoteuploader.initialized:
            # propagate the notes file path
            self.osmnoteuploader = OsmNoteHandler(notes_file_path=self.notes_file_path)
            self.osmnoteuploader.initialize_client()

    def generate_osm_note_url(self, note_id: int):
        return f"https://www.openstreetmap.org/note/{note_id}"

    def upload_note(self, point: Point):
        """Upload note based on the point and the text in the config"""
        self.initialize_note_uploader()
        note_id = self.osmnoteuploader.create_and_upload_note(point=point)
        print(f"Note uploaded, see {self.generate_osm_note_url(note_id)}")
        self.number_of_open_notes += 1

    @staticmethod
    def calculate_distance_points(row, point):
        source_lon = row["longitude"]
        source_lat = row["latitude"]
        target_point = point
        dist = distance(
            (source_lat, source_lon), (target_point.y, target_point.x)
        ).meters
        return dist

    def calculate_distance_to_previously_created_osm_notes(
        self, point: Point
    ) -> DataFrame:
        """This is a point object where y=latitude and x=longitude"""
        self.read_notes_dataframe()
        if not self.notes_df.empty:
            osm_notes_distance_df = self.notes_df.copy()

            osm_notes_distance_df["distance_to_point"] = osm_notes_distance_df.apply(
                self.calculate_distance_points,
                axis=1,
                args=(point,),
            )

            osm_notes_distance_df = osm_notes_distance_df[
                osm_notes_distance_df["distance_to_point"] <= 100
            ].sort_values(by="distance_to_point", ascending=True)

            return osm_notes_distance_df
        else:
            # Return empty dataframe
            logger.warning("No notes in the notes file")
            return DataFrame()

    def calculate_distance_to_osm_features(self, point) -> DataFrame:
        """This is a point object where y=latitude and x=longitude"""
        osm_distance_df = self.osm_df.copy()
        # Assuming 'gdf' has a geometry column named 'geometry'
        # Assuming 'target_point' is a Point object with coordinates (latitude, longitude)

        osm_distance_df["distance_to_point"] = self.osm_df.apply(
            self.calculate_distance_geopandas, axis=1, args=(point,)
        )
        # Remove rows with distance over 100 meters
        osm_distance_df = osm_distance_df.loc[
            osm_distance_df["distance_to_point"] <= 100
        ]

        # Sort by ascending distance
        return osm_distance_df.sort_values(by="distance_to_point", ascending=True)

    def iterate_source_features(self):
        """Iterate the source_df rows and work on them"""
        total_number_of_rows = len(self.source_df.index)
        for index, row in self.source_df.iterrows():
            # Access individual columns of the row as needed.
            # This is a point object where y=latitude and x=longitude
            source_point: Point = row["geometry"]  # Access the geometry of the feature.
            # NOTE: this ID is not persistent so we can't trust it
            lm_id = row["objektidentitet"]  # Access an attribute column.
            print(
                f"Working on feature {index}/{total_number_of_rows}: Geometry: {source_point}, ID: {lm_id}"
            )
            # First check if the point is withing the bounding box
            if self.bbox.is_valid:
                if not self.bbox.check_if_point_is_inside(source_point):
                    logger.debug("skipping this point because it is not inside the boundary box")
                    logger.debug(f"See {self.generate_osm_url(source_point)}")
                    if config.press_enter_to_continue:
                        input("Press enter to continue")
                    continue
                else:
                    logger.debug(f"point is inside box, See {self.generate_osm_url(source_point)}")
                    if config.press_enter_to_continue:
                        input("Press enter to continue")
            # First calculate distance to notes previously created
            notes_distance_df = self.calculate_distance_to_previously_created_osm_notes(
                point=source_point
            )
            if config.loglevel == logging.INFO:
                print("notes_distance_df")
                print(notes_distance_df)
            if notes_distance_df.empty:
                print("No note found withing 100m in OSM in the notes.csv file")
                osm_distance_df = self.calculate_distance_to_osm_features(
                    point=source_point
                )
                if osm_distance_df.empty:
                    print("No bathing site found withing 100m in OSM")
                    print(f"See {self.generate_osm_url(source_point)}")
                    if config.press_enter_to_continue:
                        input("Press enter to continue")
                    if (
                        config.upload_to_osm
                        and self.number_of_open_notes <= config.max_number_of_open_notes
                    ):
                        print(f"Open notes: {self.number_of_open_notes}")
                        print("Uploading new note")
                        self.upload_note(point=source_point)
                        #if config.press_enter_to_continue:
                        input("Press enter to continue")
                    else:
                        print(
                            "100 open notes already exists or upload was skipped in the config"
                        )
                else:
                    print("Found a bathing site already in OSM within 100m")
                    if config.loglevel == logging.INFO:
                        print("Found the following bathing sites within 100m in OSM")
                        print(osm_distance_df.head())
                    if config.press_enter_to_continue:
                        input("Press enter to continue")
            else:
                print("A note has already been created for this feature")

    def setup_argparse_and_get_filename(self):
        parser = ArgumentParser(
            description="Read and process Geojson files from the command line."
        )
        parser.add_argument(
            "--source-geojson", required=True, help="Source geojson file"
        )
        parser.add_argument("--osm-geojson", required=True, help="OSM geojson file")
        parser.add_argument("--notes-file", required=True, help="Notes csv file to use")
        parser.add_argument("--bounding-box", required=False, help="Restrict note creation to a specific area. "
                                                                   "E.g. 10.5389,53.7768,10.9262,53.9574. "
                                                                   "Generate here: http://osm.duschmarke.de/bbox.html")
        args = parser.parse_args()

        self.source_geojson = args.source_geojson
        self.osm_geojson = args.osm_geojson
        self.notes_file_path = args.notes_file
        self.bounding_box_string = args.bounding_box
