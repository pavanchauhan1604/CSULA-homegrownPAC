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
│   ├── sharepoint_sync.py       # Sync Excel to OneDrive + generate email drafts (no DB)
│   ├── send_emails.py           # Send pre-generated drafts via Outlook COM (Windows)
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

**Step 1 — Install VeraPDF manually** (required before running setup)

> `setup.ps1` will auto-detect VeraPDF and configure the path for you, but it cannot run the VeraPDF installer silently due to Windows permission restrictions. Install it once, manually:

1. Go to **https://verapdf.org/software/** and download the Windows installer ZIP
2. Extract the ZIP and run **`verapdf-install.bat`** inside the extracted folder
3. When prompted for an install location, choose a folder you own, e.g.:
   `C:\Users\<YourName>\AppData\Local\Programs\veraPDF`

**Step 2 — Clone repo and run setup**

```powershell
# 1. Clone and enter repo
git clone https://github.com/pavanchauhan1604/CSULA-homegrownPAC.git
cd CSULA-homegrownPAC

# 2. Allow PowerShell scripts (once per machine)
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 3. If you downloaded a ZIP instead of git clone, unblock the scripts first
Get-ChildItem -Recurse -Filter *.ps1 | Unblock-File

# 4. Run automated setup (installs Python 3.11, Java 21, creates venv, installs packages,
#    auto-detects VeraPDF path, configures config.py)
.\setup.ps1

# 5. Activate the virtual environment (required before running python commands)
.\.venv\Scripts\Activate.ps1
```

> `setup.ps1` will print `[!] VeraPDF not found` if it can't locate the install — re-run it after completing the VeraPDF install above.

> See [setup/WINDOWS_INSTALLATION_GUIDE.md](setup/WINDOWS_INSTALLATION_GUIDE.md) for full details and troubleshooting.

### Daily workflow

```powershell
# Full pipeline: crawl → scan → Excel → sync to OneDrive → email drafts → all reports
.\scripts\run_workflow_smooth.ps1 ; python scripts/sharepoint_sync.py ; python scripts/historical_analysis.py ; python scripts/generate_master_report.py ; python scripts/generate_master_report_html.py

# Review the HTML drafts in the OneDrive domain folders, then send when ready
python scripts/send_emails.py          # prompts for confirmation
python scripts/send_emails.py --force  # skips confirmation

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

### Sync to SharePoint/Teams and generate email drafts
```powershell
# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Sync all domains: copies Excel to OneDrive + writes {employee_id}_draft.html per domain folder
python scripts/sharepoint_sync.py

# Sync specific domains only
python scripts/sharepoint_sync.py --domains www.calstatela.edu_admissions
```

Each domain folder in OneDrive will contain:
- The latest timestamped Excel report
- One `{employee_id}_draft.html` per assigned employee (overwritten on every run)

### Generate Historical Analysis Dashboards
```powershell
# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Generate per-domain HTML trend dashboards from all timestamped reports in OneDrive
python scripts/historical_analysis.py

# Save to local output/reports/ instead of OneDrive
python scripts/historical_analysis.py --no-upload
```

### Generate Master Reports (Excel + HTML dashboard)

Both scripts write into the **`Master/`** subfolder inside your synced OneDrive
Teams folder (`Master/Master Report.xlsx` and `Master/master_report.html`).

```powershell
# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Generate both master reports in one go (Excel first, then HTML dashboard)
python scripts/generate_master_report.py ; python scripts/generate_master_report_html.py
```

Run them individually if needed:

```powershell
# Excel workbook — historical data accumulates across runs, Dashboard always shows latest
python scripts/generate_master_report.py

# HTML dashboard — fully overwritten/refreshed on every run
python scripts/generate_master_report_html.py

# HTML dashboard from a local folder instead of OneDrive
python scripts/generate_master_report_html.py --source local --local-path "C:\path\to\folder"
```

**Overwrite behaviour:**

| File | Behaviour |
|---|---|
| `Master/master_report.html` | Fully overwritten each run — always reflects current scan data |
| `Master/Master Report.xlsx` | File is overwritten, but the `Data` sheet **accumulates** one snapshot per run per domain (historical log). The `Dashboard` tab always reflects the most recent run. |

What `Master Report.xlsx` contains:
- `Data` sheet: one row per domain per run (timestamp + totals) — grows over time
- `Dashboard` sheet: always shows the latest run; includes a dropdown in `B3` to browse older run dates
- `Run Index` sheet: hidden helper sheet used by the dropdown list

What `master_report.html` contains:
- Summary pills: total domains, unique PDFs, overall compliance %, high-priority count
- Trend insight banner: how many domains are improving / declining / stable
- Snapshot bar charts: compliance % and high-priority PDFs per domain (colour-coded)
- Historical trend charts: aggregate and per-domain compliance over time (when ≥ 2 scan dates exist)
- Domain summary table and per-domain detail cards with mini trend charts

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
- **SharePoint/OneDrive Integration**: Syncs Excel reports to the Teams channel folder and generates personalised HTML email drafts per employee — no database required for the send step
- **Historical Dashboards**: Per-domain Chart.js trend dashboards comparing all timestamped scans

## Requirements

- Python 3.11+ (auto-installed by `setup.ps1`)
- Java 21+ (auto-installed by `setup.ps1`, required for VeraPDF)
- VeraPDF (**manual install required** — see Quick Start Step 1; `setup.ps1` auto-detects the path and writes it to `config.py`)
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
