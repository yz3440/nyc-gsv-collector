# London Street View Data Collector

A Python-based tool for collecting and analyzing Google Street View panorama data across London postcodes. You can modify the script to collect data from other areas.

## Overview

This project samples coordinates throughout London postcode districts and collects associated Google Street View panorama data. It uses a multi-threaded approach to efficiently gather panorama metadata including location, date, and copyright information.

## Features

- Generates coordinate grid points within London postcode boundaries
- Searches for Street View panoramas near sampled coordinates
- Collects panorama metadata (date, copyright, location, etc.)
- Multi-threaded processing for improved performance
- Progress tracking and statistics

## Prerequisites

- Python 3.x
- Google Maps API key

### Install dependencies

```bash
pip install -r requirements.txt
```

## Data Storage

All data is stored in a local SQLite database named `gsv.db`. This database is created automatically when running the scripts and maintains the state throughout the entire scraping process. The database persists between runs, allowing for interrupted scraping jobs to be resumed.

## Usage

### Sample Coordinates

```bash
python 01-sample-coordinates.py
```

This script samples coordinates throughout London postcode districts and saves them to a SQLite database. It uses a grid of points with a specified spacing (by default `5 meters`, but can be adjusted).

### Search Panoramas near Coordinates

```bash
python 02-search-and-update-metadata.py
```

This script searches for panoramas near the sampled coordinates and updates the metadata in the database. It uses a multi-threaded approach to efficiently gather panorama metadata.

### Update Panoramas with Date and Copyright

```bash
python 03-search-date-and-copyright.py
```

At the search step, we only get the panorama id, lat, lon, and heading. We need to get the date and copyright information to get a complete panorama.

### Check Progress

```bash
python 04-check-progress.py
```

While the search and update steps are running, you can use this script to check the progress.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

This project uses the following open-source packages:

- [geopandas](https://github.com/geopandas/geopandas) (BSD-3-Clause License)
- [python-dotenv](https://github.com/theskumar/python-dotenv) (BSD-3-Clause License)
- [streetview](https://github.com/robolyst/streetview)

For full license texts of dependencies, please see their respective repositories.

The London postcodes GeoJSON data in `geojson/Borough Boundaries.geojson` is from [sjwhitworth/london_geojson](https://github.com/sjwhitworth/london_geojson/blob/master/london_postcodes.json).
