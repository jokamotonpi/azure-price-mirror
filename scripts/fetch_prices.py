"""
fetch_prices.py — Azure Retail Prices fetcher
Fetches a single region passed as a CLI argument and writes
prices/AzurePriceList_<region>.csv.

Usage: python fetch_prices.py <arm-region-name>
Example: python fetch_prices.py centralus

No external packages required — stdlib only.
"""

import json
import csv
import urllib.request
import urllib.error
import os
import sys
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE = "https://prices.azure.com/api/retail/prices"
OUTPUT_DIR = "prices"
# ─────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "azure-price-mirror/1.0 (github-actions)",
}


def fetch_all_items(region: str) -> list[dict]:
    url = f"{API_BASE}?armRegionName={region}"
    all_items: list[dict] = []
    page = 0

    while url:
        page += 1
        print(f"  [{region}] page {page} — fetched {len(all_items):,} rows so far …")
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            # The API sometimes returns a NextPageLink pointing past the last row.
            # "Skip value N is greater than the total count N" means we already
            # have everything — treat it as a clean end of results, not an error.
            if e.code == 400 and "Skip value" in body and "greater than the total count" in body:
                print(f"  [{region}] reached end of results after {len(all_items):,} rows (API skip boundary — normal)")
                break
            print(f"  ERROR {e.code} on page {page}: {e.reason}")
            print(f"  URL: {url}")
            print(f"  Response body: {body[:500]}")
            raise

        all_items.extend(data.get("Items", []))
        url = data.get("NextPageLink")

    print(f"  [{region}] done — {len(all_items):,} rows")
    return all_items


def write_csv(items: list[dict], path: str) -> None:
    if not items:
        print(f"  No items — skipping {path}")
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = list(items[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(items)

    size_mb = os.path.getsize(path) / 1_048_576
    print(f"  Written: {path}  ({size_mb:.1f} MB)")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python fetch_prices.py <arm-region-name>")
        print("Example: python fetch_prices.py centralus")
        sys.exit(1)

    region = sys.argv[1].strip()
    run_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"Azure Retail Prices fetch — {region} — {run_time}")

    items = fetch_all_items(region)
    out_path = os.path.join(OUTPUT_DIR, f"AzurePriceList_{region}.csv")
    write_csv(items, out_path)
    print("All done.")


if __name__ == "__main__":
    main()
