import sys, os, re, time, requests, pandas as pd
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from typing import Optional

CSV_PATH = "grandpa house csv final.csv"
IMG_DIR  = "images"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}

os.makedirs(IMG_DIR, exist_ok=True)

def find_redfin_url(address: str) -> Optional[str]:
    query = f'"{address}" site:redfin.com'
    with DDGS() as ddgs:
        results = ddgs.text(query, region='wt-wt', safesearch='Moderate', timelimit='y', max_results=10)
        for r in results:
            href = r.get('href', '')
            if 'redfin.com' in href:
                return href.split('?')[0]
    return None

def extract_image(listing_url: str) -> Optional[str]:
    try:
        r = requests.get(listing_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        # preload link first
        link = soup.find('link', attrs={'rel':'preload', 'as':'image'})
        if link and link.get('href'):
            return link['href']
        # fallback og:image meta
        meta = soup.find('meta', property='og:image')
        if meta and meta.get('content'):
            return meta['content']
    except Exception:
        pass
    return None

def slugify(text: str, length: int = 60) -> str:
    return re.sub(r'[^A-Za-z0-9]+', '_', text)[:length].strip('_')

def scrape_address(address: str):
    print(f"Searching Redfin for: {address}")
    url = find_redfin_url(address)
    if not url:
        print("  ✗ No Redfin result via DDG")
        return None
    print(f"  ✓ Listing URL: {url}")
    img = extract_image(url)
    if not img:
        print("  ✗ No hero image found")
        return None
    print(f"  ✓ Image URL: {img}")
    # download
    fname = os.path.join(IMG_DIR, slugify(address)+'.jpg')
    try:
        resp = requests.get(img, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            with open(fname, 'wb') as f:
                f.write(resp.content)
            print(f"  ✓ Saved to {fname}\n")
            return fname
    except Exception as e:
        print("  ✗ Download failed", e)
    return None

if __name__ == '__main__':
    if len(sys.argv) > 1:
        scrape_address(' '.join(sys.argv[1:]))
    else:
        # default: first address in CSV
        df = pd.read_csv(CSV_PATH)
        first = df.iloc[0]['Full_Address']
        scrape_address(first) 