# Web Crawlers

Scrapy-based web crawlers for discovering PDFs on university websites.

## Structure

```
sf_state_pdf_scan/
├── run_all_spiders.py           # Orchestrates running multiple spiders
├── run_spider_by_name.py        # Run a single spider
├── scrapy.cfg                   # Scrapy configuration
└── sf_state_pdf_scan/
    ├── settings.py              # Spider settings (delays, concurrency)
    ├── box_handler.py           # Box.com link processor
    ├── items.py                 # Data models
    ├── pipelines.py             # Data processing pipelines
    ├── middlewares.py           # Request/response middleware
    └── spiders/
        └── faculty_spider.py    # Example spider template
```

## Creating New Spiders

1. Copy `faculty_spider.py` as a template
2. Update `name`, `start_urls`, and `output_folder`
3. Customize link extraction logic if needed

## Running Spiders

### Run all spiders sequentially:
```bash
cd crawlers/sf_state_pdf_scan
python run_all_spiders.py
```

### Run a specific spider:
```bash
cd crawlers/sf_state_pdf_scan
python run_spider_by_name.py spider_name
```

### Run with Scrapy CLI:
```bash
cd crawlers/sf_state_pdf_scan
scrapy crawl faculty_spider
```

## Output

Each spider creates a folder in the configured output directory:
```
{domain-name}/
└── scanned_pdfs.txt
```

Format: `PDF_URL PARENT_URL TIMESTAMP`

## Box.com Integration

The `box_handler.py` module automatically detects and processes Box share links:
- Extracts direct download URLs from share pages
- Checks if PDFs are downloadable
- Logs failed Box links separately
