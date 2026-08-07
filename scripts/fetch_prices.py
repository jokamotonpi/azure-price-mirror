"""
fetch_prices.py — Azure Retail Prices fetcher
Pulls all pages from the Azure Retail Prices API for the configured region
and writes a single CSV to prices/AzurePriceList_<region>.csv.

No external packages required — stdlib only.
"""

import json
import csv
import urllib.request
import os
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
REGIONS = ["eastus", "centralus"]  # add more ARM region names here if desired
API_BASE = "https://prices.azure.com/api/retail/prices"
API_VERSION = "2023-01-01-preview"
OUTPUT_DIR = "prices"
# ─────────────────────────────────────────────────────────────────────────────


def fetch_all_items(region: str) -> list[dict]:
    url = f"{API_BASE}?armRegionName={region}&api-version={API_VERSION}"
    all_items: list[dict] = []
    page = 0

    while url:
        page += 1
        print(f"  [{region}] page {page} — fetched {len(all_items):,} rows so far …")
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        all_items.extend(data.get("Items", []))
        url = data.get("NextPageLink")  # None when last page

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
    run_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"Azure Retail Prices fetch — {run_time}")

    for region in REGIONS:
        items = fetch_all_items(region)
        out_path = os.path.join(OUTPUT_DIR, f"AzurePriceList_{region}.csv")
        write_csv(items, out_path)

    print("All done.")


if __name__ == "__main__":
    main()
