# azure-price-mirror

Nightly mirror of the [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices).  
A GitHub Actions workflow runs every night at 2 AM UTC, fetches all rows for the configured region(s), and commits the result as a CSV.

## Output files

| File | Region | Updated |
|------|--------|---------|
| `prices/AzurePriceList_eastus.csv` | East US (`eastus`) | Nightly |

## CSV columns

`currencyCode`, `tierMinimumUnits`, `retailPrice`, `unitPrice`, `armRegionName`,
`location`, `effectiveStartDate`, `effectiveEndDate`, `meterId`, `meterName`,
`productId`, `skuId`, `productName`, `skuName`, `serviceName`, `serviceId`,
`serviceFamily`, `unitOfMeasure`, `type`, `isPrimaryMeterRegion`, `armSkuName`

## Adding more regions

Edit `REGIONS` in `scripts/fetch_prices.py`:

```python
REGIONS = ["eastus", "westus2", "centralus"]
```

Then push — the next workflow run will produce a CSV for each region.

## Manual trigger

Go to **Actions → Fetch Azure Prices → Run workflow** to fetch on demand.

## Source

Data is pulled directly from Microsoft's public API:  
`https://prices.azure.com/api/retail/prices?armRegionName=eastus`

No API key or authentication required.
