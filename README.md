# CSULA HomegrownPAC - PDF Accessibility Compliance System

## Overview
Automated PDF accessibility compliance system for California State University, Los Angeles (CSULA). This system crawls university websites, tests PDFs for WCAG 2.1 AA compliance, generates reports, and automates stakeholder communication.

## Project Structure

```
CSULA-homegrownPAC/
├── master_functions.py          # Main orchestrator - run workflows from here
├── config/                       # Configuration files
│   ├── priority_profiles.py     # Priority detection profiles
│   └── sites.py                 # Site configurations
├── src/                         # Source code modules
│   ├── core/                    # Core functionality
│   │   ├── database.py          # Database schema & setup
│   │   ├── conformance_checker.py # VeraPDF integration
│   │   ├── pdf_priority.py      # PDF analysis algorithms
│   │   ├── filters.py           # Priority & filtering logic
│   │   └── scan_refresh.py      # 404 checking & status updates
│   ├── data_management/         # Data import/export
│   │   ├── data_import.py       # CSV imports & database writes
│   │   ├── data_export.py       # Query execution & Excel generation
│   │   └── doa_import.py        # DOA-specific imports
│   ├── reporting/               # Report generation
│   │   └── html_report.py       # HTML dashboard generation
│   ├── communication/           # Email automation (Outlook - Windows)
│   │   ├── communications.py    # Email content generation
│   │   ├── outlook_sender.py    # Outlook COM email sending (Windows-only)
│   │   ├── pdf_email.py         # (Deprecated - reference only)
│   │   └── admin_email.py       # (Deprecated - reference only)
│   └── utilities/               # Helper utilities
│       └── tools.py             # Utility functions
├── scripts/                     # Automation scripts
│   └── send_emails.py           # Email sending script (Outlook - Windows)
├── crawlers/                    # Web scraping
│   └── sf_state_pdf_scan/       # Scrapy project
│       ├── run_all_spiders.py   # Spider orchestrator
│       └── sf_state_pdf_scan/   # Spider modules
├── sql/                         # SQL query library
│   ├── get_all_sites.sql
│   ├── get_pdf_reports_by_site_name.sql
│   └── ...
├── data/                        # CSV data files
│   ├── employees.csv
│   ├── sites.csv
│   └── site_assignments.csv
├── output/                      # Generated outputs
│   ├── reports/                 # Excel & HTML reports
│   ├── emails/                  # Email MSG files
│   └── backups/                 # Database backups
├── docs/                        # Documentation
│   └── info/                    # ADA compliance guidelines
├── temp/                        # Temporary files (PDFs, JSON)
└── drupal_pdfs.db              # SQLite database (auto-generated)
```

## Quick Start

### 1. Initial Setup
```bash
# Create database tables
python src/core/database.py

# Import employee and site data
python src/data_management/data_import.py
```

### 2. Run Full Scan
```bash
# Complete workflow: crawl → test → report
python master_functions.py
# Then call: create_all_pdf_reports()
```

### 3. Generate Reports
```bash
# Generate Excel reports for all sites
python master_functions.py
# Then call: build_all_xcel_reports()
```

### 4. Send Emails
```bash
# Send PDF accessibility reports via Outlook automation (Windows-only)
python3 scripts/send_emails.py
```

### 5. Generate HTML Dashboard
```bash
python src/reporting/html_report.py
```

## Key Features

- **Automated Web Crawling**: Scrapy spiders crawl university domains to find PDFs
- **PDF Accessibility Testing**: VeraPDF integration for PDF/UA compliance
- **Deep PDF Analysis**: Custom algorithms using pikepdf and pdfminer
- **Priority Detection**: Smart algorithms identify high-priority PDFs
- **Box.com Integration**: Special handling for Box shared links
- **Excel Report Generation**: Formatted reports with hyperlinks and validation
- **HTML Dashboard**: Comprehensive overview with metrics
- **Email Automation**: Windows Outlook desktop automation (no SMTP)
- **404 Tracking**: Monitors broken links and removed PDFs
- **Duplicate Detection**: SHA-256 hashing prevents redundant testing

## Requirements

- Python 3.x
- VeraPDF (external CLI tool)
- SQLite
- Libraries: scrapy, pikepdf, pdfminer.six, openpyxl, jinja2, beautifulsoup4, requests

### Install Python dependencies

```bash
python -m pip install -r requirements.txt
```

### Windows

For a complete Windows setup (PowerShell + venv + VeraPDF + Outlook Desktop sending), see: `setup/WINDOWS_INSTALLATION_GUIDE.md`.

## Compliance Target

**ADA Title II Compliance Deadline**: April 24, 2026

## Database Schema

See `src/core/database.py` for complete schema with 6 tables:
- `drupal_pdf_files` - PDF inventory
- `pdf_report` - Accessibility test results
- `drupal_site` - Website registry
- `site_user` - Employee/content manager info
- `site_assignment` - User-to-site mappings
- `failure` - Error log

## Support

For questions or issues, contact the Accessibility Technology Initiative (ATI).
