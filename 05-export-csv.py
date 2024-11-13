import os
import time
import sqlite3


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
# MARK: Export CSV
########################################


def export_csv():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT pano_id, lat, lon, date, copyright, heading, pitch, roll FROM search_panoramas"
    )
    rows = cursor.fetchall()
    conn.close()

    # Data is in "2024-04" format, make it "2024-04-01"
    for i, row in enumerate(rows):
        date = row[3]
        if date is None:
            continue
        date = date[:7] + "-01"
        row = list(row)
        row[3] = date
        rows[i] = tuple(row)

    delimiter = "\t"

    import csv

    with open("panoramas.csv", "w") as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(
            ["pano_id", "lat", "lon", "date", "copyright", "heading", "pitch", "roll"]
        )
        writer.writerows(
            [[value if value is not None else "NULL" for value in row] for row in rows]
        )


if __name__ == "__main__":
    setup_database()
    export_csv()
