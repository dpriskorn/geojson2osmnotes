from shapely import Point

from models.GeojsonHandler import GeojsonHandler


class TestGeojsonHandler:
    def test_calculate_distance_points(self):
        gh = GeojsonHandler()
        # This is a point object where y=latitude and x=longitude
        # invocation Point([y, x])
        print(
            gh.calculate_distance_points(
                Point(59.52921313056148, 17.83229425591725),
                Point(59.52921313056148, 17.83229425591725),
            )
        )

    # def test_calculate_distance_to_previously_created_osm_notes(self):
    #     # This should yield one row in the df
    #     gh = GeojsonHandler(notes_file_path="test_data/notes.csv", )
    #     df = gh.calculate_distance_to_previously_created_osm_notes(
    #         point=Point(59.52921313056148, 17.83229425591725)
    #     )
    #     print(df.info())
    #     assert len(df.index) == 1
