from unittest import TestCase

from shapely import Point

from models.bounding_box import BoundingBox


class TestBoundingBox(TestCase):
    """
    # This use point object where y=latitude and x=longitude
    latitude = point.y
    longitude = point.x
    """
    def test_check_if_point_is_inside_true1(self):
        bb = BoundingBox(x1=1,x2=3,y1=1,y2=3)
        assert bb.check_if_point_is_inside(Point([2,2])) is True

    def test_check_if_point_is_inside_true2(self):
        # https://www.openstreetmap.org/note/3915849
        # https://www.openstreetmap.org/#map=18/59.5292131/17.8322943
        # bounding box that should contain the point
        # 17.7835,59.4582,18.0306,59.6017
        bb = BoundingBox(x1=17.7835,
                         y1=59.4582,
                         x2=18.0306,
                         y2=59.6017)
        assert bb.check_if_point_is_inside(Point([17.8322943, 59.5292131])) is True

    def test_check_if_point_is_inside_false(self):
        # 17.7835,59.4582,18.0306,59.6017
        bb = BoundingBox(x1=17.7835,
                         y1=59.4582,
                         x2=18.0306,
                         y2=59.6017)
        assert bb.check_if_point_is_inside(Point([17.8322943, 69.5292131])) is False


    def test_is_valid_true(self):
        bb = BoundingBox(x1=1,x2=1,y1=1,y2=1)
        assert bb.is_valid is True

    def test_is_valid_false(self):
        bb = BoundingBox(x1=0,x2=1,y1=1,y2=1)
        assert bb.is_valid is False
