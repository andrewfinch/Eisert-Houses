import csv
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


def normalize_address(street: str) -> str:
    """Return a lowercase, hyphen-separated version of the street address (no city/state)."""
    # keep alphanumerics and spacing, replace other chars with space, then collapse whitespace
    street = re.sub(r"[^0-9a-zA-Z ]", " ", street)
    street = re.sub(r"\s+", " ", street).strip().lower()
    return street.replace(" ", "-")


COMMON_SUFFIXES = {
    "st",
    "street",
    "ave",
    "avenue",
    "rd",
    "road",
    "dr",
    "drive",
    "ct",
    "court",
    "blvd",
    "boulevard",
    "ln",
    "lane",
}


def strip_suffix(tokens: list[str]) -> list[str]:
    """Drop trailing token if it's a common road suffix."""
    if tokens and tokens[-1] in COMMON_SUFFIXES:
        return tokens[:-1]
    return tokens


def url_contains_address(redfin_url: str, norm_street: str) -> bool:
    """True if the normalized street tokens appear in the URL path."""
    if not redfin_url or not redfin_url.startswith("https://www.redfin.com"):
        return False
    path_tokens = [t for t in re.split(r"[/-]+", urlparse(redfin_url).path.lower()) if t]

    addr_tokens_full = norm_street.split("-")

    # Check for exact match with suffix (if any)
    try:
        idx = path_tokens.index(addr_tokens_full[0])
        if path_tokens[idx : idx + len(addr_tokens_full)] == addr_tokens_full:
            return True
    except ValueError:
        pass

    # If the address itself lacks a suffix, allow path to have one (i.e., match without last token)
    if addr_tokens_full[-1] not in COMMON_SUFFIXES:
        addr_tokens_short = addr_tokens_full
    else:
        # Address had a suffix; do not accept mismatch.
        return False

    # For suffixless address, try match again without relying on path suffix presence
    try:
        idx = path_tokens.index(addr_tokens_short[0])
    except ValueError:
        return False

    return path_tokens[idx : idx + len(addr_tokens_short)] == addr_tokens_short


def clean_csv(path: Path, output: Optional[Path] = None) -> None:
    output = output or path

    with path.open(newline="", encoding="utf-8") as f_in, output.open(
        "w", newline="", encoding="utf-8"
    ) as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames or []
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            # Extract & normalize street portion of the address (everything before first comma)
            full_addr = row.get("Full_Address", "")
            street_part = full_addr.split(",")[0]
            norm_street = normalize_address(street_part)

            redfin_url = row.get("Redfin_URL", "")
            if not url_contains_address(redfin_url, norm_street):
                # Bad match: wipe the Redfin URL & image link
                row["Redfin_URL"] = ""
                if "Redfin_Image" in row:
                    row["Redfin_Image"] = ""
            writer.writerow(row)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_redfin_csv.py input_csv [output_csv]")
        sys.exit(1)

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    clean_csv(in_path, out_path) 