"""
Läs in alla badplatser från Topo50
Läs in alla badplatser via overpass som geojson
För varje badplats i Topo50
  Kolla om badplats finns inom 100m i OSM
  Om badplats inte finns:
     Kolla om not finns i närheten 100m via APIn
     Om not finns:
        Skriv ut Länk till noten
        Vänta på user input
      Om inte finns:
        Logga in/autentisera
        Skapa not med innehållet nedan
        Debug: vänta på input och kolla manuellt att allt blev rätt

Fråga chatgpt hur jag bäst beräknar närheten
av badplatser i osm för varje punkt i topo50 dataframen.
Min gissning är att göra en ny dataframe med distanskolumn
 för varje topo50 punkt och beräkna distansen till alla
  badplatser i osm och filtrera bort allt över 100 m.
Är det feasible?
"""
import logging
from argparse import ArgumentParser

import geopandas  # type:ignore
from geopy.distance import distance  # type:ignore
from pandas import DataFrame
from pydantic import BaseModel
from shapely import Point

import config
from models.osm_note_uploader import OsmNoteUploader

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)


class GeometryError(BaseException):
    pass


class GeojsonHandler(BaseModel):
    """This class takes care of setting up the
    # get source geojson and osmfeatures geojson from the command line
    # parse with geopandas
    # for every source feature:
      check if it already exists in osm within 100m
    """

    source_geojson: str = ""
    osm_geojson: str = ""
    source_df: DataFrame = DataFrame()
    osm_df: DataFrame = DataFrame()
    osmnoteuploader = OsmNoteUploader()

    class Config:
        arbitrary_types_allowed = True

    def start(self):
        self.setup_argparse_and_get_filename()
        self.create_geodataframes()
        self.iterate_source_features()
        raise NotImplementedError()

    def create_geodataframes(self):
        """Create geodataframes based on the geojson input files"""
        self.source_df = geopandas.read_file(self.source_geojson)
        print(self.source_df.info())
        # exit()
        self.osm_df = geopandas.read_file(self.osm_geojson)

    @staticmethod
    def calculate_distance(row, target_point):
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
        latitude = point.y
        longitude = point.x
        return f"https://www.openstreetmap.org/#map=19/{latitude}/{longitude}"

    def initialize_note_uploader(self):
        if not self.osmnoteuploader.initialized:
            self.osmnoteuploader = OsmNoteUploader()
            self.osmnoteuploader.initialize_client()

    def generate_osm_note_url(self, note_id: int):
        return f"https://www.openstreetmap.org/note/{note_id}"

    def upload_note(self, point: Point):
        self.initialize_note_uploader()
        note_id = self.osmnoteuploader.create_and_upload_note(point=point)
        print(f"Note uploaded, see {self.generate_osm_note_url(note_id)}")

    def iterate_source_features(self):
        """Iterate the source_df rows and work on them"""
        for index, row in self.source_df.iterrows():
            # Access individual columns of the row as needed.
            geometry = row["geometry"]  # Access the geometry of the feature.
            lm_id = row["objektidentitet"]  # Access an attribute column.

            # Perform operations or calculations with the geometry and attributes.
            # For example, you can print the geometry and an attribute value.
            print(f"Feature {index} - Geometry: {geometry}, Id: {lm_id}")
            osm_distance_df = self.osm_df
            # Assuming 'gdf' has a geometry column named 'geometry'
            # Assuming 'target_point' is a Point object with coordinates (latitude, longitude)

            osm_distance_df["distance_to_point"] = self.osm_df.apply(
                self.calculate_distance, axis=1, args=(geometry,)
            )
            # Remove rows with distance over 100 meters
            osm_distance_df = osm_distance_df.loc[
                osm_distance_df["distance_to_point"] <= 100
            ]

            # Sort by ascending distance
            osm_distance_df = osm_distance_df.sort_values(
                by="distance_to_point", ascending=True
            )
            if osm_distance_df.empty:
                print("No bathing site found withing 100m in OSM")
                print(f"See {self.generate_osm_url(geometry)}")
                input("Press enter to continue")
                if config.upload_to_osm:
                    # todo check if a note exists already near this position
                    print("Uploading new note")
                    self.upload_note()
                    exit()
                    input("Press enter to continue")
                else:
                    print("Skipping upload")
            else:
                print("Found the following bathing sites within 100m in OSM")
                print(osm_distance_df.head())
                input("Press enter to continue")

    def setup_argparse_and_get_filename(self):
        parser = ArgumentParser(
            description="Read and process Geojson files from the command line."
        )
        parser.add_argument(
            "--source-geojson", required=True, help="Source geojson file"
        )
        parser.add_argument("--osm-geojson", required=True, help="OSM geojson file")
        args = parser.parse_args()

        self.source_geojson = args.source_geojson
        self.osm_geojson = args.osm_geojson


if __name__ == "__main__":
    logger.info("Starting")
    ls = GeojsonHandler()
    ls.start()
