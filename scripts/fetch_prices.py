"""
fetch_prices.py — Azure Retail Prices fetcher
Fetches a single region passed as a CLI argument and writes
prices/AzurePriceList_<region>.csv.

Usage: python fetch_prices.py <arm-region-name>
Example: python fetch_prices.py centralus

No external packages required — stdlib only.

IMPORTANT: The Azure Retail Prices API requires the OData $filter syntax to
properly restrict results to a single region.  The shorthand query-string form
(?armRegionName=X) does NOT filter — it returns the entire global price list
(~1 M rows, ~268 MB), which exceeds GitHub's 100 MB push limit.

Correct URL form:
  https://prices.azure.com/api/retail/prices?$filter=armRegionName eq 'centralus'&$skip=N
"""

import json
import csv
import urllib.request
import urllib.error
import urllib.parse
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
    # Use OData $filter to restrict results to the requested region only.
    # The $skip parameter is used for manual pagination because NextPageLink
    # is unreliable when responses are very large.
    filter_expr = f"armRegionName eq '{region}'"
    base_url = f"{API_BASE}?$filter={urllib.parse.quote(filter_expr)}"

    all_items: list[dict] = []
    skip = 0
    page = 0

    while True:
        page += 1
        url = f"{base_url}&$skip={skip}"
        print(f"  [{region}] page {page} (skip={skip}) — fetched {len(all_items):,} rows so far …")

        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # HTTP 400 after page 1 = skip value exceeded total count (end of data)
            if e.code == 400 and page > 1:
                print(f"  [{region}] HTTP 400 on page {page} — end of results, "
                      f"{len(all_items):,} rows collected.")
                break
            print(f"  ERROR {e.code} on page {page}: {e.reason}")
            raise

        items = data.get("Items", [])
        if not items:
            print(f"  [{region}] Empty page — end of results.")
            break

        all_items.extend(items)
        skip += len(items)

        # Belt-and-suspenders: also follow NextPageLink if present and skip
        # value aligns, but prefer our own skip counter.
        next_link = data.get("NextPageLink")
        if not next_link:
            # No next page link — done
            break

    print(f"  [{region}] done — {len(all_items):,} total rows")
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
