import os
import time
import sqlite3
import streetview
import concurrent.futures

DB_PATH = "gsv.db"

SEARCH_BATCH_SIZE = 100000

# if you are skeptical about the API results affected by the network, you can set this to False
# and the coords that have no panorama found will not be marked as searched, and will be searched again in the future
COUNT_NONE_FOUND_AS_SEARCHED = True

WORKERS = 36


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
# MARK: Get unsearched coords
########################################


def get_unsearched_coords(batch_size: int) -> dict[int, tuple[float, float]]:
    conn = sqlite3.connect(DB_PATH)
    coords: dict[int, tuple[float, float]] = {}

    cursor = conn.execute(
        "SELECT id, lat, lon, label, searched FROM sample_coords WHERE searched = 0 ORDER BY RANDOM() LIMIT ?",
        [batch_size],
    )

    rows = cursor.fetchall()

    print(f"Found {len(rows)} unsearched coords")

    for row in rows:
        (id, lat, lon, label, searched) = row
        coords[id] = (lat, lon)

    conn.close()

    return coords


########################################
# MARK: Search panorama
########################################


def search_and_insert(coord_id, lat, lon):

    print(f"Searching for coords {coord_id} with lat {lat:.2f} and lon {lon:.2f}")
    panorama_results = streetview.search_panoramas(lat, lon)

    # if result is not a list or is an empty list
    if not isinstance(panorama_results, list):
        print(f"Error searching for point {coord_id}, ({lat}, {lon})")
        return

    if len(panorama_results) == 0:
        print(f"No panorama found for point {coord_id}, ({lat}, {lon})")
        if not COUNT_NONE_FOUND_AS_SEARCHED:
            return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for result in panorama_results:
        cursor.execute(
            "INSERT OR IGNORE INTO search_panoramas VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                result.pano_id,
                result.lat,
                result.lon,
                result.date,
                None,
                result.heading,
                result.pitch,
                result.roll,
            ],
        )
    cursor.execute("UPDATE sample_coords SET searched = 1 WHERE id = ?", [coord_id])
    conn.commit()
    conn.close()

    print(f"Found {len(panorama_results)} panoramas for coord {coord_id}")


def run_batch_in_parallel():
    coords = get_unsearched_coords(SEARCH_BATCH_SIZE)

    if len(coords) == 0:
        print("No unsearched coords found, exiting")
        exit(0)

    coords_count = len(coords)

    progress = 0
    begin_time = time.time()
    last_progress_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(search_and_insert, coord_id, lat, lon): coord_id
            for coord_id, (lat, lon) in coords.items()
        }

        for future in concurrent.futures.as_completed(futures):
            coord_id = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error searching for coord {coord_id}")
                print(e)
            progress += 1
            last_duration = time.time() - last_progress_time
            last_speed = 1 / last_duration
            last_progress_time = time.time()
            total_duration = time.time() - begin_time
            total_speed = progress / total_duration
            # clear the console
            os.system("cls" if os.name == "nt" else "clear")
            print("Search Coord Progress: %d/%d" % (progress, coords_count))
            print("Last Speed: %f coords/sec" % last_speed)
            print("Total Speed: %f coords/sec" % total_speed)


if __name__ == "__main__":
    setup_database()

    while True:
        run_batch_in_parallel()
