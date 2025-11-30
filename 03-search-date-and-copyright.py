import os
import time
import sqlite3
import streetview
import concurrent.futures
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "gsv.db"
GOOGLE_MAP_API_KEY = os.getenv("GOOGLE_MAP_API_KEY")

if GOOGLE_MAP_API_KEY is None:
    raise ValueError("GOOGLE_MAP_API_KEY is not set")

SEARCH_BATCH_SIZE = 100000


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
# MARK: Get panoramas without date and copyright
########################################


def get_panoramas_without_date_and_copyright(batch_size: int) -> list[str]:
    conn = sqlite3.connect(DB_PATH)
    panoramas = []

    cursor = conn.execute(
        "SELECT * FROM search_panoramas WHERE date IS NULL OR date = '' OR copyright IS NULL OR copyright = '' ORDER BY RANDOM() LIMIT ?",
        [batch_size],
    )

    rows = cursor.fetchall()

    print(f"Found {len(rows)} panoramas without date and copyright")

    for row in rows:
        (pano_id, lat, lon, date, copyright, heading, pitch, roll) = row
        panoramas.append(pano_id)

    conn.close()

    return panoramas


########################################
# MARK: Search and update metadata
########################################


def search_and_update(pano_id):

    print(f"Searching for panorama {pano_id}")
    
    try:
        metadata = streetview.get_panorama_meta(pano_id, GOOGLE_MAP_API_KEY)
    except Exception as e:
        print(f"API error for {pano_id}: {e}")
        return

    if metadata is None or (metadata.date is None and metadata.copyright is None):
        print("No meta found for %s" % pano_id)
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE search_panoramas SET date = ?, copyright = ? WHERE pano_id = ?",
        [metadata.date, metadata.copyright, pano_id],
    )
    conn.commit()
    conn.close()

    print(f"Updated metadata for {pano_id}")


def run_batch_in_parallel():
    panoramas = get_panoramas_without_date_and_copyright(SEARCH_BATCH_SIZE)

    if len(panoramas) == 0:
        print("No panoramas without date and copyright found, exiting")
        exit(0)

    panorama_count = len(panoramas)

    progress = 0
    begin_time = time.time()
    last_progress_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = {
            executor.submit(search_and_update, pano_id): pano_id
            for pano_id in panoramas
        }

        for future in concurrent.futures.as_completed(futures):
            pano_id = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error searching for panorama {pano_id}")
                print(e)
            progress += 1
            last_duration = time.time() - last_progress_time
            last_speed = 1 / last_duration
            last_progress_time = time.time()
            total_duration = time.time() - begin_time
            total_speed = progress / total_duration

            # clear the console
            os.system("cls" if os.name == "nt" else "clear")
            print("Search Panorama Progress: %d/%d" % (progress, panorama_count))
            print("Last Speed: %f panoramas/sec" % last_speed)
            print("Total Speed: %f panoramas/sec" % total_speed)


if __name__ == "__main__":
    setup_database()

    while True:
        run_batch_in_parallel()
