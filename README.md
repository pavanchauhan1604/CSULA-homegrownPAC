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
│   ├── send_emails.py           # Email sending script (Outlook - Windows)
│   ├── teams_upload.py          # Copy Excel reports to Teams via OneDrive sync
│   └── historical_analysis.py  # Per-domain HTML trend dashboards
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

### First time on a new machine

```powershell
# 1. Clone and enter repo
git clone https://github.com/pavanchauhan1604/CSULA-homegrownPAC.git
cd CSULA-homegrownPAC

# 2. Allow PowerShell scripts (once per machine)
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 3. If you downloaded a ZIP instead of git clone, unblock the scripts first
Get-ChildItem -Recurse -Filter *.ps1 | Unblock-File

# 4. Run automated setup (installs Python, Java, VeraPDF, venv, packages, configures paths)
.\setup.ps1
```

> See [setup/WINDOWS_INSTALLATION_GUIDE.md](setup/WINDOWS_INSTALLATION_GUIDE.md) for full details and troubleshooting.

### Daily workflow

```powershell
# Run the full pipeline (crawl -> analyze -> Excel reports -> email HTML)
.\scripts\run_workflow_smooth.ps1

# Send emails via Outlook Desktop
.\scripts\send_emails.ps1 -Force

# Check scan progress while pipeline is running
.\scripts\check_progress.ps1

# Reset to a clean slate (backs up DB, clears all outputs)
.\scripts\fresh_start.ps1
```

### Managing domains

Edit **`data/sites.csv`** to add or remove domains (full URLs, one per line):

```csv
https://www.calstatela.edu/admissions,CSULA-content-manager_pchauha5
https://www.calstatela.edu/financialaid,CSULA-content-manager_jsmith
```

### Upload Reports to Teams (OneDrive)
```powershell
# Copies the latest Excel report for each domain into the synced Teams channel folder
python scripts/teams_upload.py

# Upload specific domains only
python scripts/teams_upload.py --domains www.calstatela.edu_admissions
```

### Generate Historical Analysis Dashboards
```powershell
# Generate per-domain HTML trend dashboards from all timestamped reports in OneDrive
python scripts/historical_analysis.py

# Save to local output/reports/ instead of OneDrive
python scripts/historical_analysis.py --no-upload
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
- **Teams/OneDrive Integration**: Copies Excel reports into the synced Teams channel folder; generates per-domain HTML trend dashboards comparing all historical timestamped scans

## Requirements

- Python 3.11+ (auto-installed by `setup.ps1`)
- Java 21+ (auto-installed by `setup.ps1`, required for VeraPDF)
- VeraPDF (auto-downloaded and installed by `setup.ps1`)
- SQLite
- Libraries: scrapy, pikepdf, pdfminer.six, openpyxl, jinja2, beautifulsoup4, requests (all installed from `requirements.txt` by `setup.ps1`)

### Windows setup

Run `.\setup.ps1` from the project root. See [setup/WINDOWS_INSTALLATION_GUIDE.md](setup/WINDOWS_INSTALLATION_GUIDE.md) for details.

### Teams / OneDrive Setup

`setup.ps1` auto-detects and writes `TEAMS_ONEDRIVE_PATH` in `config.py` if the *"PDF Accessibility Checker (PAC) - General"* Teams channel folder is already synced via OneDrive. Domain subfolders are created automatically on first upload.

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
