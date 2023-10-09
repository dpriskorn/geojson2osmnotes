import logging

from pydantic import BaseModel
from shapely import Point

logger = logging.getLogger(__name__)


class BoundingBox(BaseModel):
    x1: float = 0.0
    x2: float= 0.0
    y1: float= 0.0
    y2: float= 0.0

    def check_if_point_is_inside(self, point: Point):
        """Check if a point is inside the bounding box"""
        x = point.x # longitude
        y = point.y # latitude
        # adapted from https://stackoverflow.com/a/61294889
        if self.x1 < x < self.x2:
            logger.debug(f"longitude coordinate {x} is inside box "
                         f"defined by x1: {self.x1} and x2: {self.x2}")
            if self.y1 < y < self.y2:
                logger.debug(f"latitude coordinate {y} is inside box "
                             f"defined by y1: {self.y1} and y2: {self.y2}")
                return True
        return False

    @property
    def is_valid(self):
        if self.x1 > 0 and self.x2 > 0 and self.y1 > 0 and self.y2 > 0:
            return True
        return False
