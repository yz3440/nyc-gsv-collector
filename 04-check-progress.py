import os
import time
import sqlite3
import streetview
import concurrent.futures
import os


DB_PATH = "gsv.db"


########################################
# MARK: Database setup
########################################


def setup_database():
    print("Setting up database")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS sample_coords
            (id INTEGER PRIMARY KEY AUTOINCREMENT, lat real, lon real, label text, searched boolean default False)
            """
    )
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS search_panoramas (
        pano_id TEXT PRIMARY KEY,
        lat REAL,
        lon REAL,
        date TEXT,
        copyright TEXT,
        heading REAL,
        pitch REAL,
        roll REAL
    )
    """
    )

    conn.commit()
    conn.close()


########################################
# MARK: Get counts
########################################


def count_unsearched_points():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT COUNT(*) FROM sample_coords WHERE searched = 0")
    res = cursor.fetchone()
    conn.close()
    return res[0]


def count_total_points():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT COUNT(*) FROM sample_coords")
    res = cursor.fetchone()
    conn.close()
    return res[0]


def count_total_panoramas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT COUNT(*) FROM search_panoramas")
    res = cursor.fetchone()
    conn.close()
    return res[0]


def count_panoramas_with_date_and_copyright():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT COUNT(*) FROM search_panoramas WHERE date IS NOT NULL AND date != '' AND copyright IS NOT NULL AND copyright != ''"
    )
    res = cursor.fetchone()
    conn.close()
    return res[0]


if __name__ == "__main__":
    setup_database()

    unsearched_points = count_unsearched_points()
    total_points = count_total_points()
    searched_points = total_points - unsearched_points
    point_search_progress = searched_points / total_points

    total_panoramas = count_total_panoramas()
    panoramas_with_date_and_copyright = count_panoramas_with_date_and_copyright()
    panoramas_metadata_progress = panoramas_with_date_and_copyright / total_panoramas

    panorama_points_ratio = total_panoramas / searched_points

    print(
        f"Point Search Progress: {point_search_progress*100:.2f}% \t {searched_points}/{total_points}"
    )

    print(
        f"Found {total_panoramas} panoramas ({panorama_points_ratio:.4f} pano per point)"
    )

    print(
        f"Panorama Metadata Progress: {panoramas_metadata_progress*100:.2f}% \t {panoramas_with_date_and_copyright}/{total_panoramas}"
    )

    print(f"Expected {total_points * panorama_points_ratio:.1f} panoramas")
