#!/usr/bin/env python3
"""
Geocode every address in Grandpa-Houses main.csv
and write latitude & longitude back to a new file.

Prerequisites
-------------
pip install pandas requests
export GOOGLE_API_KEY='YOUR-KEY-HERE'  # optional if using Google API
"""

import os
import time
import requests
import pandas as pd
from typing import Optional, Tuple  # Added for type annotations compatible with Python 3.9

# ---------- USER CONFIG  -----------------------------------------
CSV_IN   = "Grandpa-Houses main.csv"
CSV_OUT  = "Grandpa-Houses geocoded.csv"
ADDR_COL = "Full_Address"          # change if your column name differs
API_KEY  = " "  # MUST be set for Google geocoding
PAUSE_BETWEEN_CALLS = 1.0          # seconds (friendly for free services like Nominatim)
# ----------------------------------------------------------------

if not API_KEY:
    raise RuntimeError("Please set your Google Geocoding API key as the GOOGLE_API_KEY environment variable.")

def geocode(address: str) -> Tuple[Optional[float], Optional[float]]:
    """Return (lat, lng) or (None, None) if no result."""
    if pd.isna(address) or not address:
        return None, None
    # ---------- Google Geocoding attempt ----------
    if API_KEY:
        endpoint = (
            "https://maps.googleapis.com/maps/api/geocode/json"
            f"?address={requests.utils.quote(address)}&key={API_KEY}"
        )
        try:
            r = requests.get(endpoint, timeout=10)
            r.raise_for_status()
            data = r.json()
            status = data.get("status")
            if status == "OK" and data["results"]:
                loc = data["results"][0]["geometry"]["location"]
                return loc["lat"], loc["lng"]
            else:
                # Log detailed error once per unique status to help troubleshooting
                err_msg = data.get("error_message", "")
                print(f"[WARN] Google status '{status}' for '{address}'. {err_msg}")
        except requests.RequestException as exc:
            print(f"[WARN] Google geocoding failed for '{address}': {exc}")

    # ---------- OpenStreetMap Fallback ----------
    try:
        nom_url = "https://nominatim.openstreetmap.org/search"
        params  = {"q": address, "format": "json", "limit": 1}
        headers = {"User-Agent": "EisertHousesGeocoder/1.0"}
        r2 = requests.get(nom_url, params=params, headers=headers, timeout=10)
        if r2.status_code == 200:
            res = r2.json()
            if res:
                return float(res[0]["lat"]), float(res[0]["lon"])
    except requests.RequestException as exc:
        print(f"[WARN] OSM geocoding failed for '{address}': {exc}")

    return None, None

# ---------- MAIN ------------------------------------------------
df = pd.read_csv(CSV_IN)

lats, lngs = [], []
for addr in df[ADDR_COL]:
    lat, lng = geocode(addr)
    lats.append(lat)
    lngs.append(lng)
    time.sleep(PAUSE_BETWEEN_CALLS)   # polite pacing

df["Latitude"]  = lats
df["Longitude"] = lngs
df.to_csv(CSV_OUT, index=False)
print(f"✓ Geocoded file written to {CSV_OUT}")