import pandas as pd
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from typing import Optional
import time

INPUT_CSV = "grandpa house csv final.csv"
OUTPUT_CSV = "grandpa house csv redfin.csv"
ADDR_COL = "Full_Address"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    )
}
PAUSE = 1.5  # seconds between queries (be polite)


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
    df = pd.read_csv(INPUT_CSV)
    if "Redfin_URL" not in df.columns:
        df["Redfin_URL"] = ""
    if "Redfin_Image" not in df.columns:
        df["Redfin_Image"] = ""

    for idx, row in df.iterrows():
        addr = row[ADDR_COL]
        if pd.isna(addr):
            continue
        if row.get("Redfin_Image"):
            continue  # already done

        print(f"Processing: {addr} …", end=" ")
        listing = find_redfin_listing(addr)
        if not listing:
            print("no listing found")
            continue
        img = extract_hero_image(listing) or ""
        df.at[idx, "Redfin_URL"] = listing
        df.at[idx, "Redfin_Image"] = img
        print("✓", "(img)" if img else "(no img)")
        time.sleep(PAUSE)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved enriched data to {OUTPUT_CSV}")


if __name__ == "__main__":
    main() 