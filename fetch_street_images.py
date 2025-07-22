#!/usr/bin/env python3
"""Append a Google Street View Static API image URL to each row.

This uses *only* Google’s officially supported Static Street View API, so it’s
within their Terms of Service (no scraping).  You must supply your own API key
in an environment variable:

    export GOOGLE_STREETVIEW_KEY="YOUR_GOOGLE_KEY"

Then run:

    python fetch_street_images.py source.csv dest.csv

Google’s free tier currently allows 25 000 Street View *image* requests per
project per day.  Your file has ≈300 rows, so you’re well under the limit.
Quota and pricing can change; always check your GCP console.
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from typing import Optional

import requests

GOOGLE_URL = (
    "https://maps.googleapis.com/maps/api/streetview"
    "?size=640x640&location={lat},{lon}&fov=80&pitch=0&key={key}"
)


def google_streetview_image(lat: str, lon: str, key: str) -> str:
    return GOOGLE_URL.format(lat=lat, lon=lon, key=key)


def enrich_csv(src: Path, dst: Path) -> None:
    g_key = os.getenv("GOOGLE_STREETVIEW_KEY")
    if not g_key:
        print("[ERROR] GOOGLE_STREETVIEW_KEY environment variable not set.")
        sys.exit(1)

    with src.open(newline="", encoding="utf-8") as fin, dst.open(
        "w", newline="", encoding="utf-8"
    ) as fout:
        rdr = csv.DictReader(fin)
        fieldnames = rdr.fieldnames or []
        if "Street_Image_URL" not in fieldnames:
            fieldnames.append("Street_Image_URL")
        wtr = csv.DictWriter(fout, fieldnames=fieldnames)
        wtr.writeheader()

        for row in rdr:
            lat, lon = row.get("Latitude"), row.get("Longitude")
            if lat and lon:
                row["Street_Image_URL"] = google_streetview_image(lat, lon, g_key)
            else:
                row["Street_Image_URL"] = ""
            wtr.writerow(row)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python fetch_street_images.py source.csv dest.csv")
        sys.exit(1)
    enrich_csv(Path(sys.argv[1]), Path(sys.argv[2])) 