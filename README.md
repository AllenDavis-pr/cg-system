# Price Analysis System

A Django-based pricing tool for second-hand retailers. Scrapes competitor prices, uses AI to suggest optimal pricing, and automates item listings.

## What it does

- Scans barcodes to get product info
- Scrapes prices from CashConverters, CashGenerator, CEX, and eBay
- Uses Google Gemini AI to suggest selling prices
- Tracks inventory and links items to market categories
- Automates listing process with Playwright

## Main features

### Individual item analysis
POST to `/analyze-item/` with:
```json
{
  "item_name": "MacBook Air 2022",
  "description": "13-inch, good condition"
}
```

Returns AI pricing suggestion with competitor data.

### Bulk analysis
POST to `/bulk-analyze/` with multiple items for batch processing.

### Barcode scanning
POST to `/scan-barcodes/` with barcode list to get product details.

### Inventory management
- Link inventory items to market categories
- Track serial numbers and descriptions
- Manage stock status

## Configuration
Configure exclude keywords per market item to filter out irrelevant listings.

## File structure

- `views.py` - Main logic and API endpoints
- `automation/scraper_utils.py` - Price scraping functions
- `automation/playwright_listing.py` - Automated listing script
- `automation/scrape_nospos.py` - Barcode scanning

## Notes

- AI uses temperature=0.0 for consistent pricing
- Scraper runs automatically when no competitor data exists
