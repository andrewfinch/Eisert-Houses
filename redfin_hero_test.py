import sys
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from typing import Optional

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    )
}

def find_redfin_listing(address: str) -> Optional[str]:
    query = f'{address} redfin'
    with DDGS() as ddgs:
        for result in ddgs.text(query, max_results=20):
            url = result.get("href", "")
            if "redfin.com" in url:
                return url.split("?")[0]
    return None

def extract_hero_image(url: str) -> Optional[str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        preload = soup.find("link", attrs={"rel": "preload", "as": "image"})
        if preload and preload.get("href"):
            return preload["href"]
        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            return meta["content"]
    except Exception as e:
        print("Error fetching hero image:", e)
    return None

def main():
    address = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "4260 SW Council Crest Dr, Portland, OR"
    print("Address:", address)
    listing_url = find_redfin_listing(address)
    if not listing_url:
        print("No Redfin listing found via DuckDuckGo")
        return
    print("Listing URL:", listing_url)
    hero = extract_hero_image(listing_url)
    if hero:
        print("Hero Image:", hero)
    else:
        print("Hero image not found on listing page")

if __name__ == "__main__":
    main() 