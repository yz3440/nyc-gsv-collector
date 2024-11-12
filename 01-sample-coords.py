import geopandas as gpd
import numpy as np
from shapely.geometry import Point
from shapely.prepared import prep
import os
import time
import sqlite3

# allegedly the Google Street View API will return the nearest panorama within 50 meters radius
# but I'm sampling every 5 meters, because I've seen missing panoramas in the past
SAMPLE_INTERVAL_METER = 5
# 1 degree is approximately 111000 meters
SAMPLE_INTERVAL_DEGREE = SAMPLE_INTERVAL_METER / 111000

PRINT_INTERVAL = 1000  # print every 1000 points
DB_PATH = "gsv.db"

geojson_path = "geojson/sf.geojson"

gdf = gpd.read_file(geojson_path)
print(gdf.head())

feature_dict = {}
for i, feature in gdf.iterrows():
    # make feature a new gdf
    feature_gdf = gpd.GeoDataFrame([feature])
    feature_dict[feature["neighborhood"]] = feature_gdf

print("Feature dict: ", feature_dict.keys())


def create_point_grid(bounds, interval):
    x = np.arange(bounds[0], bounds[2], interval)
    y = np.arange(bounds[1], bounds[3], interval)
    xx, yy = np.meshgrid(x, y)
    points = [Point(x, y) for x, y in zip(xx.ravel(), yy.ravel())]
    return points


def get_points_in_polygon(points, polygon, label):
    start_time = time.time()
    elapsed_time = 0.000001
    points_in_polygon = []
    for i, point in enumerate(points):
        if i % PRINT_INTERVAL == 0:
            print("Processing %s" % label)
            print("Checking point %d/%d" % (i, len(points)))
            print("Points in polygon: ", len(points_in_polygon))
            print("Elapsed time: %.2f seconds" % elapsed_time)
            speed = (i + 1) / elapsed_time
            print("Speed: %.2f points/sec" % speed)
            remaining_points = len(points_in_bbox) - i
            remaining_time = remaining_points / speed
            print("Remaining time: %.2f seconds" % remaining_time)
        if polygon.contains(point):
            points_in_polygon.append(point)

        elapsed_time = time.time() - start_time

        if i % PRINT_INTERVAL == PRINT_INTERVAL - 1 or i == len(points) - 1:
            os.system("cls" if os.name == "nt" else "clear")

    return points_in_polygon


def save_points_to_db(points, label):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS sample_coords
                (id INTEGER PRIMARY KEY AUTOINCREMENT, lat real, lon real, label text, searched boolean default False)"""
    )
    conn.commit()

    # Insert a row of data
    for point in points:
        cursor.execute(
            "INSERT INTO sample_coords VALUES (NULL, ?, ?, ?, ?)",
            (point.y, point.x, label, False),
        )
    conn.commit()
    conn.close()


for borough in feature_dict.keys():
    print("Processing borough: ", borough)
    gdf = feature_dict[borough]

    # each borough is a multi-polygon, so we need to explode it into individual polygons
    gdf = gdf.explode(index_parts=True)
    print("Exploded gdf: ", gdf.head())

    points_in_borough = []

    # make each individual polygon a new gdf
    for polygon_idx, polygon in enumerate(gdf["geometry"]):
        process_label = f"{borough} - polygon {polygon_idx}"
        print("Processing %s" % process_label)

        polygon_gdf = gpd.GeoDataFrame([polygon], columns=["geometry"])
        bb = polygon_gdf.total_bounds
        polygon_prepared = prep(polygon)

        # sample points in the bounding box based on INTERVAL
        points_in_bbox = create_point_grid(bb, SAMPLE_INTERVAL_DEGREE)

        print(f"Total points in bounding box: {len(points_in_bbox)}")

        points_in_polygon = get_points_in_polygon(
            points_in_bbox, polygon_prepared, process_label
        )
        print(f"Total points in {process_label}: {len(points_in_polygon)}")
        points_in_borough.extend(points_in_polygon)

    print(f"Total points in {borough}: {len(points_in_borough)}")
    print("Saving points to db")
    save_points_to_db(points_in_borough, borough)
