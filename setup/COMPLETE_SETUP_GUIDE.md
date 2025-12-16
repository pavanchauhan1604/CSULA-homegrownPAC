# CSULA PDF Accessibility Checker - Complete Setup & Run Guide

**Last Updated:** October 27, 2025

This is the **ONLY** guide you need to set up and run the CSULA PDF Accessibility Checker from scratch.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Configuration](#configuration)
4. [Running the Workflow](#running-the-workflow)
5. [Understanding Results](#understanding-results)
6. [Troubleshooting](#troubleshooting)

---

## 1️⃣ Prerequisites

### System Requirements
- **Operating System:** macOS, Linux, or Windows
- **Python:** Version 3.11 or higher
- **Disk Space:** At least 2GB free

### Required Software

#### Install Python 3.11+
```bash
# Check your Python version
python3 --version

# If you need to install Python 3.11+, visit:
# https://www.python.org/downloads/
```

#### Install VeraPDF (Required for PDF Analysis)
```bash
# macOS (using Homebrew)
brew install verapdf

# Linux
wget https://software.verapdf.org/releases/verapdf-installer.zip
unzip verapdf-installer.zip
./verapdf-install

# Windows
# Download from: https://verapdf.org/software/
# Run the installer and add to PATH
```

Verify VeraPDF installation:
```bash
verapdf --version
# Should show: veraPDF 1.28.0 or higher
```

---

## 2️⃣ Initial Setup

### Step 1: Navigate to Project Directory
```bash
# macOS/Linux example
cd /path/to/CSULA-homegrownPAC

# Windows (PowerShell) example
# cd C:\path\to\CSULA-homegrownPAC
```

### Step 2: Install Python Packages

Recommended: use a virtual environment and install from `requirements.txt`.

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Required Packages:**
- `scrapy` - Web crawling framework
- `requests` - HTTP library
- `beautifulsoup4` - HTML parsing
- `lxml` - XML processing
- `openpyxl` - Excel file generation
- `jinja2` - HTML report templating
- `pandas` - DOA imports / data handling
- `pikepdf` - PDF manipulation
- `pdfminer.six` - PDF text extraction
- `chardet` - Character encoding detection
- `urllib3` - HTTP client

**Windows-only:**
- `pywin32` - required for Outlook Desktop email automation (installed automatically on Windows)

**Verify Installation:**
```bash
python -c "import scrapy, requests, openpyxl; print('All packages installed successfully!')"
```

### Step 3: Make Scripts Executable

This step is **macOS/Linux only**. Windows users can skip this.

```bash
chmod +x scripts/run_workflow.sh
chmod +x scripts/fresh_start.sh
chmod +x scripts/check_progress.sh
```

---

## 3️⃣ Configuration

### Understanding the Configuration File

All settings are in **`config.py`** at the project root. You only need to edit this file.

### Key Settings to Configure

#### 1. Institution Settings
```python
# Institution domain suffix (e.g., "calstatela.edu" for CSULA)
INSTITUTION_DOMAIN = "calstatela.edu"

# Institution name (for reports and communications)
INSTITUTION_NAME = "Cal State LA"

# Test email recipient (for development/testing)
TEST_EMAIL_RECIPIENT = "your.email@calstatela.edu"
```

#### 2. Test Domains (Most Important!)

This controls which domains to scan. For testing, start with 1-3 domains:

```python
# Test domains (for initial testing with a subset of domains)
TEST_DOMAINS = [
    "calstatela.edu",              # Main site
    # "www-adminfin.calstatela.edu",  # Uncomment to add more
    # "academicsenate.calstatela.edu", # Uncomment to add more
]

# Use test domains only (set to False for production)
USE_TEST_DOMAINS_ONLY = True
```

**⚠️ Important:**
- For your **first run**, use only 1 domain
- After verifying it works, add more domains
- Set `USE_TEST_DOMAINS_ONLY = False` for production (scans ALL domains in database)

#### 3. CSV Files Configuration

The system uses CSV files in the `data/` folder to define:
- **sites.csv** - List of domains and their security groups
- **employees.csv** - List of employees who manage domains
- **managers.csv** - List of employee IDs who are managers
- **site_assignments.csv** - Assignment of employees to domains

**Format of sites.csv:**
```csv
calstatela.edu,CSULA-d-main-site-content-manager
www-adminfin.calstatela.edu,CSULA-d-adminfin-content-manager
```

**Format of employees.csv:**
```csv
Full Name,Employee ID,Email
Pavan Chauhan,123456,pchauha5@calstatela.edu
Jane Smith,234567,jane.smith@calstatela.edu
```

**Format of managers.csv:**
```csv
123456
234567
```

**Format of site_assignments.csv:**
```csv
CSULA-d-main-site-content-manager,Pavan Chauhan,123456,pchauha5@calstatela.edu
CSULA-d-adminfin-content-manager,Jane Smith,234567,jane.smith@calstatela.edu
```

**Note:** The `scripts/setup_test_environment.py` script automatically creates these CSV files based on your `TEST_DOMAINS` configuration. You typically don't need to edit them manually.

---

## 4️⃣ Running the Workflow

### Quick Start (Recommended)

**For a fresh start (cleans everything):**
```bash
cd /path/to/CSULA-homegrownPAC
./scripts/fresh_start.sh && ./scripts/run_workflow.sh
```

**Windows:** use the step-by-step commands in `setup/WINDOWS_INSTALLATION_GUIDE.md` (the `.sh` scripts are not used on Windows).

This will:
1. Clean all previous data (database, output files, temp files)
2. Run the complete workflow from scratch

### Step-by-Step Workflow

The workflow consists of 7 steps:

#### **Step 0: Setup Database and Load Test Data**
```bash
python3 scripts/setup_test_environment.py
```
- Creates database tables
- Generates CSV files from `config.py` settings
- Loads domains, users, and assignments into database

#### **Step 1: Generate Spiders**
```bash
python3 config/generate_spiders.py
```
- Creates Scrapy spiders for each domain in the database
- One spider per domain

#### **Step 2: Crawl Websites to Find PDFs**
```bash
cd crawlers/sf_state_pdf_scan && python3 run_all_spiders.py
```
- Crawls each domain (up to 3 levels deep)
- Finds all PDF links
- Saves results to `output/scans/{domain}/scanned_pdfs.txt`
- **Time:** 5-15 minutes per domain

#### **Step 3: Check Crawl Results**
```bash
find output/scans -name 'scanned_pdfs.txt' -exec wc -l {} +
```
- Shows how many PDFs were found per domain

#### **Step 4: Analyze PDFs for Accessibility**
```bash
python3 master_functions.py
```
- Downloads each PDF
- Runs VeraPDF validation
- Analyzes accessibility violations
- Stores results in database
- **Time:** 30-60 minutes (depends on number of PDFs)

#### **Step 5: Generate Excel Reports**
```bash
python3 -c "
from master_functions import build_all_xcel_reports
build_all_xcel_reports()
"
```
- Creates Excel files with PDF scan results
- Saves to `output/scans/{domain}/{domain}-pdf-scans.xlsx`

#### **Step 6: Generate Email Reports**
```bash
python3 -c "
from master_functions import build_emails
build_emails()
"
```
- Creates HTML email reports for each domain manager
- Saves to `output/emails/email_{name}.html`

#### **Step 7: View Results**
```bash
# Open Excel reports
open output/scans/*/*.xlsx

# Open email previews
open output/emails/*.html

# Query database
sqlite3 drupal_pdfs.db
```

### Monitoring Progress

While the workflow is running, you can check progress:
```bash
./scripts/check_progress.sh
```

This shows:
- Number of PDFs found
- Number of PDFs analyzed
- Current status

---

## 5️⃣ Understanding Results

### Database Structure

The system uses SQLite database (`drupal_pdfs.db`) with 6 tables:

1. **drupal_site** - List of domains
2. **drupal_pdf_files** - All PDF files found (with parent pages)
3. **pdf_report** - Accessibility analysis results
4. **site_user** - List of employees
5. **site_assignment** - Employee-to-domain assignments
6. **failure** - Failed PDF analysis attempts

### Output Files

#### Excel Reports (`output/scans/{domain}/{domain}-pdf-scans.xlsx`)
Contains 3 worksheets:
- **Scanned PDFs** - All PDFs with analysis results
  - Columns: PDF URL, Parent Page, Date, Violations, Failed Checks, etc.
  - Clickable hyperlinks for easy access
- **Failure** - PDFs that failed analysis
- **Sheet** - Summary statistics

#### Email Reports (`output/emails/email_{name}.html`)
- Formatted HTML email ready to send
- Shows PDFs needing attention
- Grouped by domain
- Cal State LA branding

### Key Metrics

**From workflow summary:**
- **Total PDFs found:** Raw count from web crawl
- **PDFs analyzed:** Unique PDFs successfully analyzed
- **PDFs with violations:** Number showing accessibility issues
- **Average violations:** Mean violations per PDF

**Typical Results:**
- 90-95% of PDFs have accessibility violations
- Average 4-6 violations per PDF
- Most common issues: Missing tags, missing language setting, no title

---

## 6️⃣ Troubleshooting

### Common Issues

#### Issue: "No such table: drupal_site"
**Solution:** Run the database setup first:
```bash
python3 scripts/setup_test_environment.py
```

#### Issue: "verapdf: command not found"
**Solution:** Install VeraPDF:
```bash
brew install verapdf  # macOS
# Or download from https://verapdf.org
```

#### Issue: "All spiders have already completed"
**Solution:** Clean the temp files:
```bash
./scripts/fresh_start.sh
```

#### Issue: SSL Certificate Errors
**Solution:** The system automatically disables SSL verification for problematic certificates. This is already configured in the code.

#### Issue: PDFs Not Being Analyzed
**Possible causes:**
1. PDFs are behind authentication
2. PDFs are on external domains (Box.com, SharePoint)
3. PDFs are too large (>100MB)

**Solution:** Check the `failure` table in the database:
```bash
sqlite3 drupal_pdfs.db "SELECT * FROM failure LIMIT 10;"
```

#### Issue: Duplicate PDFs in Results
**This is normal!** The same PDF may appear on multiple pages. The system tracks:
- Each PDF + Parent Page combination
- Unique PDF URLs

The analysis only runs once per unique PDF.

### Useful Database Queries

```bash
# Open database
sqlite3 drupal_pdfs.db

# Count total PDFs found
SELECT COUNT(*) FROM drupal_pdf_files;

# Count unique PDFs
SELECT COUNT(DISTINCT pdf_uri) FROM drupal_pdf_files;

# Count analyzed PDFs
SELECT COUNT(*) FROM pdf_report;

# Show PDFs with most violations
SELECT pdf_hash, violations 
FROM pdf_report 
ORDER BY violations DESC 
LIMIT 10;

# Show domains and PDF counts
SELECT 
    s.domain_name, 
    COUNT(p.id) as pdf_count 
FROM drupal_site s 
LEFT JOIN drupal_pdf_files p ON s.id = p.drupal_site_id 
GROUP BY s.domain_name;
```

### Getting Help

If you encounter issues:

1. Check the `verification_report.txt` file for diagnostics
2. Review terminal output for error messages
3. Check `output/scans/{domain}/scanned_pdfs.txt` to see if PDFs were found
4. Query the database to check data

---

## 📚 Quick Reference

### Essential Commands

```bash
# Fresh start (clean everything and run)
./scripts/fresh_start.sh && ./scripts/run_workflow.sh

# Run complete workflow (without cleaning)
./scripts/run_workflow.sh

# Check progress
./scripts/check_progress.sh

# Clean everything for fresh start
./scripts/fresh_start.sh

# View configuration
python3 -c "import config; config.print_config()"

# Open Excel reports
open output/scans/*/*.xlsx

# Open email previews
open output/emails/*.html
```

### Directory Structure

```
CSULA-homegrownPAC/
├── config.py                    # MAIN CONFIGURATION FILE
├── master_functions.py          # Main workflow orchestrator
├── scripts/                     # Executable scripts
│   ├── run_workflow.sh         # Complete workflow automation
│   ├── fresh_start.sh          # Clean and reset everything
│   ├── check_progress.sh       # Monitor progress
│   └── setup_test_environment.py  # Database setup
├── setup/                       # Setup documentation
│   └── COMPLETE_SETUP_GUIDE.md # This file
├── config/                      # Spider generation
│   ├── generate_spiders.py
│   ├── priority_profiles.py
│   └── sites.py
├── data/                        # CSV data files
│   ├── sites.csv
│   ├── employees.csv
│   ├── managers.csv
│   └── site_assignments.csv
├── output/                      # Results
│   ├── scans/{domain}/         # Excel reports and crawl results
│   └── emails/                 # HTML email reports
├── crawlers/                    # Scrapy web crawlers
│   └── sf_state_pdf_scan/
├── src/                         # Core functionality
│   ├── core/                   # PDF analysis, database
│   ├── data_management/        # Data import/export
│   ├── reporting/              # Report generation
│   ├── communication/          # Email generation
│   └── utilities/              # Helper functions
├── sql/                         # SQL query files
├── temp/                        # Temporary files
└── drupal_pdfs.db              # SQLite database
```

---

## 🎯 Production Deployment

When ready to run on all domains:

1. **Update config.py:**
   ```python
   USE_TEST_DOMAINS_ONLY = False
   ```

2. **Load all domains into database:**
   - Edit `data/sites.csv` with all domains
   - Run `python3 scripts/setup_test_environment.py`

3. **Run workflow:**
   ```bash
   ./scripts/run_workflow.sh
   ```

4. **Schedule regular scans:**
   ```bash
   # Add to crontab for weekly scans (every Monday at 2 AM)
   0 2 * * 1 cd /Users/pavan/Work/CSULA-homegrownPAC && ./scripts/fresh_start.sh && ./scripts/run_workflow.sh
   ```

---

## 📝 Notes

- **First run:** Takes 1-2 hours depending on number of PDFs
- **Database:** Grows to ~10-50MB for typical university
- **Results:** Excel files are 50-200KB each
- **Crawl depth:** Limited to 3 levels to avoid infinite loops
- **PDF limits:** Skips PDFs larger than 100MB
- **External PDFs:** Box.com and SharePoint PDFs are tracked but may not be accessible

---

**For questions or issues, refer to the Troubleshooting section or check the project documentation.**
