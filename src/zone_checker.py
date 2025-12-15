# src/zone_checker.py
import cv2
import numpy as np

def is_point_in_any_zone(point, zones):
    for zone in zones:
        points = np.array(zone["points"], dtype=np.int32)
        if cv2.pointPolygonTest(points, point, False) >= 0:
            return True
    return False

def draw_zones(frame, zones):
    for zone in zones:
        points = np.array(zone["points"], dtype=np.int32)
        cv2.polylines(frame, [points], isClosed=True, color=(0, 0, 255), thickness=2)
    return frame