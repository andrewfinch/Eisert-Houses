import pandas as pd
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from typing import Optional
import time
import os

INPUT_CSV = "grandpa house csv final.csv"
OUTPUT_CSV = "grandpa house csv redfin.csv"
ADDR_COL = "Full_Address"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    )
}
PAUSE = 1.5

def find_redfin_listing(address: str) -> Optional[str]:
    query = f"{address} redfin"
    with DDGS() as ddgs:
        for result in ddgs.text(query, max_results=15):
            href = result.get("href", "")
            if "redfin.com" in href:
                return href.split("?")[0]
    return None

def extract_hero_image(listing_url: str) -> Optional[str]:
    try:
        r = requests.get(listing_url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        preload = soup.find("link", attrs={"rel": "preload", "as": "image"})
        if preload and preload.get("href"):
            return preload["href"]
        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            return meta["content"]
    except Exception:
        pass
    return None

def main():
    # Load existing output or start fresh
    if os.path.exists(OUTPUT_CSV):
        df = pd.read_csv(OUTPUT_CSV)
        print(f"Resuming from existing {OUTPUT_CSV}")
    else:
        df = pd.read_csv(INPUT_CSV)
        df["Redfin_URL"] = ""
        df["Redfin_Image"] = ""

    for idx, row in df.iterrows():
        addr = row[ADDR_COL]
        if pd.isna(addr):
            continue
            
        # Check if already processed (handle NaN properly)
        current_img = row.get("Redfin_Image", "")
        if pd.notna(current_img) and current_img != "":
            continue  # already done

        print(f"Processing: {addr} ... ", end="")
        listing = find_redfin_listing(addr)
        if not listing:
            print("no listing found")
            df.to_csv(OUTPUT_CSV, index=False)  # save even when skipping
            continue
            
        img = extract_hero_image(listing) or ""
        df.at[idx, "Redfin_URL"] = listing
        df.at[idx, "Redfin_Image"] = img
        print("✓", "(img)" if img else "(no img)")

        # Save progress after each row
        df.to_csv(OUTPUT_CSV, index=False)
        time.sleep(PAUSE)

    print(f"Completed run. Saved enriched data to {OUTPUT_CSV}")

if __name__ == "__main__":
    main() 