# CSULA PDF Accessibility Checker - Complete Setup & Run Guide

**Last Updated:** February 2026

This guide covers setup and operation of the CSULA PDF Accessibility Checker.

> **Windows users:** The easiest way to get started is `.\setup.ps1` — it automates everything (Python, Java, VeraPDF, virtual environment, packages, and path configuration). See [WINDOWS_INSTALLATION_GUIDE.md](WINDOWS_INSTALLATION_GUIDE.md).

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
- **Operating System:** Windows 10/11
- **Disk Space:** At least 2GB free

### Setup (Windows)

Run `.\setup.ps1` from the project root. It will automatically install Python 3.11, Java 21, VeraPDF, create the virtual environment, and install all packages. See [WINDOWS_INSTALLATION_GUIDE.md](WINDOWS_INSTALLATION_GUIDE.md) for step-by-step instructions.

---

## 2️⃣ Initial Setup

### Step 1: Clone and enter the project directory
```powershell
git clone https://github.com/pavanchauhan1604/CSULA-homegrownPAC.git
cd CSULA-homegrownPAC
```

### Step 2: Run automated setup
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\setup.ps1
```

This installs Python, Java, VeraPDF, creates `.venv`, installs all packages, and writes `VERAPDF_COMMAND` and `TEAMS_ONEDRIVE_PATH` into `config.py`.

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
https://www.calstatela.edu/admissions,CSULA-content-manager_pchauha5
https://www.calstatela.edu/financialaid,CSULA-content-manager_jsmith
```

Add or remove domains by editing this file. Full `https://` URLs are required.

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

```powershell
.\scripts\run_workflow_smooth.ps1
```

This runs all 7 steps automatically. For a completely clean run first:

```powershell
.\scripts\fresh_start.ps1
.\scripts\run_workflow_smooth.ps1
```

### Step-by-Step Workflow

The workflow consists of 7 steps (all handled automatically by `.\scripts\run_workflow_smooth.ps1`):

#### **Step 0: Setup Database and Load Data**
```powershell
python scripts/setup_test_environment.py
```

#### **Step 1: Generate Spiders**
```powershell
python config/generate_spiders.py
```

#### **Step 2: Crawl Websites to Find PDFs**
```powershell
cd crawlers\sf_state_pdf_scan; python run_all_spiders.py; cd ..\..
```
- Crawls each domain (up to 3 levels deep)
- **Time:** 5-15 minutes per domain

#### **Step 3: Analyze PDFs for Accessibility**
```powershell
python master_functions.py
```
- Runs VeraPDF validation on each PDF
- **Time:** 30-60 minutes (depends on number of PDFs)

#### **Step 4: Generate Excel Reports**
```powershell
python -c "from master_functions import build_all_xcel_reports; build_all_xcel_reports()"
```

#### **Step 5: Generate Email Reports**
```powershell
python -c "from master_functions import build_emails; build_emails()"
```

#### **Step 6: View Results**
```powershell
explorer .\output\scans
explorer .\output\emails
```

### Monitoring Progress

```powershell
.\scripts\check_progress.ps1
```

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

## Quick Reference

### Essential Commands

```powershell
# Fresh start (clean everything and run)
.\scripts\fresh_start.ps1
.\scripts\run_workflow_smooth.ps1

# Run complete workflow (without cleaning)
.\scripts\run_workflow_smooth.ps1

# Check progress
.\scripts\check_progress.ps1

# Send emails via Outlook Desktop
.\scripts\send_emails.ps1 -Force

# View configuration
python -c "import config; config.print_config()"

# Open results in File Explorer
explorer .\output\scans
explorer .\output\emails
```

### Directory Structure

```
CSULA-homegrownPAC/
├── config.py                    # Central configuration (auto-written by setup.ps1)
├── setup.ps1                    # One-time machine setup
├── master_functions.py          # Main workflow orchestrator
├── scripts/                     # PowerShell scripts
│   ├── run_workflow_smooth.ps1  # Complete workflow automation
│   ├── fresh_start.ps1          # Clean and reset everything
│   ├── check_progress.ps1       # Monitor progress
│   ├── send_emails.ps1          # Send emails via Outlook Desktop
│   └── setup_test_environment.py
├── setup/                       # Setup documentation
│   └── COMPLETE_SETUP_GUIDE.md # This file
├── config/                      # Spider generation
│   └── generate_spiders.py
├── data/                        # CSV data files
│   ├── sites.csv                # Domain list (full URLs) -- edit to add/remove domains
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
└── drupal_pdfs.db              # SQLite database (auto-generated)
```

---

## Production Deployment

When ready to run on all domains:

1. **Edit `data/sites.csv`** to include all domains (full `https://` URLs)

2. **Update `config.py`:**
   ```python
   USE_TEST_DOMAINS_ONLY = False
   ```

3. **Run workflow:**
   ```powershell
   .\scripts\run_workflow_smooth.ps1
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
