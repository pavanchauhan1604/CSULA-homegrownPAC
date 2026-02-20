# AUTOMATED WORKFLOW GUIDE
## CSULA PDF Accessibility Checker - Shell Script Execution

**Last Updated:** November 3, 2025  
**Version:** 1.0

---

## OVERVIEW

This guide provides step-by-step instructions for running the CSULA PDF Accessibility Checker using automated shell scripts. These scripts streamline the entire workflow from initial setup to report generation and email distribution.

---

## TABLE OF CONTENTS

1. [Prerequisites](#prerequisites)
2. [Script Overview](#script-overview)
3. [Initial Setup (One-Time)](#initial-setup-one-time)
4. [Complete Workflow Execution](#complete-workflow-execution)
5. [Individual Script Usage](#individual-script-usage)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Options](#advanced-options)

---

## PREREQUISITES

### Required Software
- ✅ **Python 3.9+** installed and in PATH
- ✅ **VeraPDF 1.28.0** installed (`/opt/homebrew/bin/verapdf` or in PATH)
- ✅ **Git** (for version control)
- ✅ **Terminal access** (macOS Terminal, iTerm2, or similar)

### Required Files
- ✅ `data/sites.csv` - Domain configuration file
- ✅ `data/employees.csv` - Employee roster (optional)
- ✅ `data/site_assignments.csv` - Site-employee mappings (optional)

### Verify Installation
```bash
# Check Python version
python3 --version
# Should show: Python 3.9.x or higher

# Check VeraPDF installation
verapdf --version
# Should show: VeraPDF 1.28.0 or compatible

# Check Git
git --version
# Should show: git version 2.x.x
```

---

## SCRIPT OVERVIEW

### Available Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `scripts/fresh_start.sh` | Clean slate - backup DB, clear outputs, truncate reports | First run or complete reset |
| `scripts/run_workflow.sh` | Main workflow - scan, analyze, generate reports | Regular PDF scanning |
| `scripts/send_emails.py` | Generate HTML emails for distribution | After reports are generated |
| `scripts/check_progress.sh` | Monitor crawling progress | During long-running scans |
| `scripts/teams_upload.py` | Copy latest Excel reports to Teams via OneDrive sync | After reports are generated |
| `scripts/historical_analysis.py` | Generate per-domain HTML trend dashboards from all historical scans | After multiple scan cycles |

---

## INITIAL SETUP (ONE-TIME)

### Step 1: Clone and Navigate to Repository

```bash
# Clone repository (if not already done)
git clone https://github.com/pavanchauhan1604/CSULA-homegrownPAC.git
cd CSULA-homegrownPAC

# Or navigate to existing directory
cd /path/to/CSULA-homegrownPAC
```

### Step 2: Configure Test Domains

Edit `config.py` to set your test domain(s):

```bash
# Open config.py in your editor
nano config.py
# or
code config.py
```

Update these settings:
```python
# Test domains (for initial testing)
TEST_DOMAINS = [
    "www.calstatela.edu_accessibility",  # Example domain
    # Add more test domains as needed
]

# Use test domains only (set to False for production)
USE_TEST_DOMAINS_ONLY = True  # Keep True for testing
```

### Step 3: Prepare Data Files

Copy example CSV files and customize:

```bash
# Copy example files
cp data/employees.csv.example data/employees.csv
cp data/site_assignments.csv.example data/site_assignments.csv

# Edit with your institution's data
nano data/employees.csv
nano data/site_assignments.csv
```

**Note:** Sites are configured in `config/sites.py`

### Step 4: Make Scripts Executable

```bash
# Make all scripts executable
chmod +x scripts/*.sh
chmod +x scripts/*.py

# Verify permissions
ls -la scripts/
```

### Step 5: Initialize Database

```bash
# Initialize database schema
python3 -c "
from src.core.database import *
print('Database initialized successfully!')
"

# Verify database created
ls -lh drupal_pdfs.db
```

---

## COMPLETE WORKFLOW EXECUTION

### Full Workflow: Fresh Start → Analysis → Reports → Emails

#### Step 1: Fresh Start (Clean Slate)

```bash
cd /Users/pavan/Work/CSULA-homegrownPAC

# Run fresh start script
./scripts/fresh_start.sh
```

**What this does:**
- ✅ Backs up current database with timestamp
- ✅ Clears all output directories (scans, emails, reports)
- ✅ Truncates `pdf_report` and `failure` tables
- ✅ Prepares system for new scan

**Expected Output:**
```
🔄 Starting fresh PDF scan workflow...
💾 Backing up database...
✅ Database backed up to: drupal_pdfs.db.backup.20251103_135000
🧹 Cleaning output directories...
✅ Output directories cleaned
🗑️  Truncating old reports...
✅ Reports table truncated
✅ Fresh start complete! Ready for new scan.
```

**Time:** ~5 seconds

---

#### Step 2: Run Complete Workflow

```bash
# Run main workflow script
./scripts/run_workflow.sh
```

**What this does:**
1. **Crawling** - Spider crawls configured domains for PDF links
2. **Analysis** - Downloads and analyzes PDFs with VeraPDF
3. **Status Refresh** - Checks PDF/parent URL accessibility
4. **Removal Tracking** - Marks PDFs no longer on website
5. **Report Generation** - Creates Excel reports with priority classification

**Expected Output:**
```
🚀 Running PDF accessibility workflow...

🕷️  Step 1: Running web crawlers...
[Scrapy output - crawling progress]
✅ Crawling complete

🔍 Step 2: Analyzing PDFs with VeraPDF...
[Analysis progress for each PDF]
✅ Analysis complete

🔄 Step 3: Refreshing PDF/parent URL status...
[Status checking progress]
✅ Status refresh complete

🗑️  Step 4: Marking removed PDFs...
✅ Removed PDFs marked

📊 Step 5: Generating Excel reports...
[Report generation for each domain]
✅ Reports generated

✅ Workflow complete!
📂 Reports available in: output/scans/
📧 Run 'python3 scripts/send_emails.py' to generate emails
```

**Time:** 
- Small domain (10-50 PDFs): 5-15 minutes
- Medium domain (50-200 PDFs): 15-45 minutes
- Large domain (200+ PDFs): 45+ minutes

---

#### Step 3: Generate Emails

```bash
# Generate HTML emails for distribution
python3 scripts/send_emails.py
```

**What this does:**
- ✅ Queries database for PDFs by employee assignment
- ✅ Generates HTML email summaries (count-based, not full table)
- ✅ Saves emails to `output/emails/`
- ✅ Opens emails in browser for manual sending

**Interactive Mode:**
```
================================================================================
📧 EMAIL GENERATION - CSULA PDF Accessibility Checker
================================================================================

🔨 Generating HTML emails...
✅ Generated 5 email(s)
📁 Saved to: /Users/pavan/Work/CSULA-homegrownPAC/output/emails

Open emails in browser for sending? (y/n): y

📧 Opening: email_jdoe_at_calstatela_edu.html
Press Enter when ready to open next email...
[Browser opens with email content]

📧 Opening: email_jsmith_at_calstatela_edu.html
Press Enter when ready to open next email...
[Continue for all emails]

================================================================================
MANUAL SENDING INSTRUCTIONS:
================================================================================
1. Copy all content from browser (Cmd+A, Cmd+C)
2. Go to: https://outlook.office365.com
3. Click 'New message'
4. Paste content (Cmd+V)
5. Add subject: '[Domain] PDF Accessibility Report'
6. Attach Excel file from output/scans/[domain]/
7. Send email
================================================================================
```

**Time:** ~2 minutes + manual sending time

---

#### Step 4: Upload Reports to Teams (OneDrive)

```bash
# Upload latest Excel report for every domain into the Teams channel folder
python scripts/teams_upload.py

# Upload specific domains only
python scripts/teams_upload.py --domains www.calstatela.edu_admissions
```

**What this does:**
- ✅ Locates the most-recent timestamped `.xlsx` for each domain in `output/scans/`
- ✅ Copies it into the matching subfolder inside the locally-synced Teams channel folder (`TEAMS_ONEDRIVE_PATH` in `config.py`)
- ✅ Creates the domain subfolder automatically if it does not yet exist
- ✅ OneDrive sync handles propagation to the shared Teams channel

**Prerequisites:**
- Teams channel must be synced to OneDrive (right-click the channel → *Sync*)
- `TEAMS_ONEDRIVE_PATH` in `config.py` must point to the local sync folder

**Expected Output:**
```
[teams_upload] Uploading reports to: C:\Users\pchauha4\OneDrive - Cal State LA\PDF Accessibility Checker (PAC) - General
[teams_upload]   calstatela-edu_admissions  -> copied  www.calstatela.edu_admissions-2025-11-03_14-00-00.xlsx
[teams_upload]   calstatela-edu_library     -> copied  www.calstatela.edu_library-2025-11-03_14-01-05.xlsx
[teams_upload] Done. 2 domain(s) processed.
```

**Time:** ~5 seconds

---

#### Step 5: Generate Historical Analysis Dashboards

```bash
# Generate per-domain HTML trend dashboards from all timestamped reports in OneDrive
python scripts/historical_analysis.py

# Save dashboards to local output/reports/<domain>/ instead of OneDrive
python scripts/historical_analysis.py --no-upload

# Specific domains only
python scripts/historical_analysis.py --domains www.calstatela.edu_admissions
```

**What this does:**
- ✅ Reads every timestamped `.xlsx` file found in each domain’s OneDrive subfolder
- ✅ Extracts key metrics per scan: total PDFs, unique PDFs, compliance %, violation counts, top error types
- ✅ Generates a self-contained `historical_analysis_{timestamp}.html` with Chart.js trend graphs
- ✅ Saves the HTML back into the same domain subfolder (or `output/reports/<domain>/` with `--no-upload`)
- ✅ Shows a table of all scans and a “Only one scan on record” message when charts aren’t yet meaningful

**Expected Output:**
```
[historical_analysis] Reading reports from: C:\Users\pchauha4\OneDrive - Cal State LA\PDF Accessibility Checker (PAC) - General
[historical_analysis]   calstatela-edu_admissions: 3 scan(s) found
[historical_analysis]     -> saved historical_analysis_2025-11-03_14-10-00.html
[historical_analysis] Done. 2 domain(s) processed.
```

**Time:** ~10 seconds

---

## INDIVIDUAL SCRIPT USAGE

### Script 1: Fresh Start Only

**Use Case:** Reset system without running full workflow

```bash
./scripts/fresh_start.sh
```

**Options:**
```bash
# Fresh start with verbose output
bash -x ./scripts/fresh_start.sh
```

---

### Script 2: Workflow Without Fresh Start

**Use Case:** Re-run workflow on existing data (update existing reports)

```bash
./scripts/run_workflow.sh
```

**Skips:**
- Database truncation (updates existing records instead)
- Output directory cleanup

---

### Script 3: Check Crawling Progress

**Use Case:** Monitor long-running crawler operations

```bash
./scripts/check_progress.sh
```

**Output:**
```
================================================================================
📊 CRAWLER PROGRESS CHECK
================================================================================
Checking: output/scans/www-calstatela-edu_accessibility/scanned_pdfs.txt

PDFs found so far: 42
Last update: 2025-11-03 13:45:32

Sample PDFs:
- https://www.calstatela.edu/file1.pdf
- https://www.calstatela.edu/file2.pdf
- https://www.calstatela.edu/file3.pdf
...

ℹ️  Crawler still running. Check again in a few minutes.
================================================================================
```

**Usage:**
```bash
# Run once
./scripts/check_progress.sh

# Monitor continuously (every 30 seconds)
watch -n 30 ./scripts/check_progress.sh
```

---

### Script 4: Email Generation Only

**Use Case:** Regenerate emails after modifying reports

```bash
python3 scripts/send_emails.py
```

**Options:**
```bash
# Generate emails without opening in browser
python3 scripts/send_emails.py --no-browser

# Generate for specific employee
python3 scripts/send_emails.py --employee "12345678"
```

---

### Script 5: Teams Upload Only

**Use Case:** Upload the latest Excel reports to Teams after a scan without re-running the full workflow

```bash
python scripts/teams_upload.py
```

**Options:**
```bash
# Upload specific domains only
python scripts/teams_upload.py --domains www.calstatela.edu_admissions www.calstatela.edu_library
```

---

### Script 6: Historical Analysis Only

**Use Case:** Regenerate trend dashboards after new reports have been uploaded

```bash
python scripts/historical_analysis.py
```

**Options:**
```bash
# Save HTML to local output/reports/ instead of OneDrive
python scripts/historical_analysis.py --no-upload

# Specific domains only
python scripts/historical_analysis.py --domains www.calstatela.edu_admissions

# Use a custom local folder as the report source
python scripts/historical_analysis.py --source local --local-path "C:/Downloads/reports"
```

---

## TROUBLESHOOTING

### Common Issues and Solutions

#### Issue 1: Permission Denied

**Error:**
```
bash: ./scripts/fresh_start.sh: Permission denied
```

**Solution:**
```bash
# Make scripts executable
chmod +x scripts/*.sh scripts/*.py

# Verify permissions
ls -la scripts/
```

---

#### Issue 2: VeraPDF Not Found

**Error:**
```
verapdf: command not found
```

**Solution:**
```bash
# Check if VeraPDF is installed
which verapdf

# If not found, install VeraPDF
brew install verapdf  # macOS with Homebrew

# Or update PATH in config.py
nano config.py
# Change: VERAPDF_COMMAND = "/full/path/to/verapdf"
```

---

#### Issue 3: Database Locked

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Check for running processes
ps aux | grep python

# Kill any stuck processes
kill -9 <PID>

# Or restart fresh
./scripts/fresh_start.sh
```

---

#### Issue 4: No PDFs Found

**Error:**
```
✅ Crawling complete
PDFs found: 0
```

**Solution:**
```bash
# Check domain configuration
cat config/sites.py

# Verify domain is accessible
curl -I https://www.calstatela.edu/accessibility

# Check crawler output
cat output/scans/www-calstatela-edu_accessibility/scanned_pdfs.txt

# Run crawler manually with verbose output
cd crawlers/sf_state_pdf_scan
scrapy crawl calstatela_edu_accessibility_spider -L DEBUG
```

---

#### Issue 5: Email Generation Fails

**Error:**
```
No employees found with PDFs
```

**Solution:**
```bash
# Check site assignments
cat data/site_assignments.csv

# Verify employees imported
sqlite3 drupal_pdfs.db "SELECT COUNT(*) FROM site_user;"

# Import employees if needed
python3 -c "
from src.data_management.data_import import add_employees_from_csv_file
add_employees_from_csv_file('data/employees.csv')
"
```

---

#### Issue 6: Workflow Hangs During Analysis

**Symptoms:**
- Script stops responding during Step 2
- No output for several minutes

**Solution:**
```bash
# Press Ctrl+C to stop

# Check for problematic PDFs
ls -lh temp/

# Run with timeout protection (already implemented)
# Or skip problematic PDF manually:
sqlite3 drupal_pdfs.db "
UPDATE drupal_pdf_files 
SET pdf_returns_404 = 1 
WHERE pdf_uri = 'https://problematic-url.pdf';
"

# Resume workflow

If the workflow was interrupted (e.g., laptop shutdown), you can rerun the
workflow script.

Important: the workflow setup step resets `drupal_pdfs.db`. The scripts are
configured to skip database rebuild when an existing DB is found, so rerunning
will resume using what was already crawled/analyzed.

./scripts/run_workflow.sh
```

---

## ADVANCED OPTIONS

### Option 1: Single Domain Workflow

Run workflow for specific domain only:

```bash
# Edit config.py
nano config.py

# Set:
TEST_DOMAINS = ["www.calstatela.edu_accessibility"]
USE_TEST_DOMAINS_ONLY = True

# Run workflow
./scripts/run_workflow.sh
```

---

### Option 2: Parallel Domain Processing

Process multiple domains simultaneously:

```bash
# Run crawlers in parallel
./scripts/run_workflow.sh &
PID1=$!

# Wait for completion
wait $PID1

echo "All workflows complete!"
```

---

### Option 3: Scheduled Automation (Cron Job)

Run workflow automatically every month:

```bash
# Edit crontab
crontab -e

# Add line (runs on 1st of each month at 2 AM):
0 2 1 * * cd /Users/pavan/Work/CSULA-homegrownPAC && ./scripts/fresh_start.sh && ./scripts/run_workflow.sh > /tmp/pdf_scan.log 2>&1
```

---

### Option 4: Custom Workflow

Create custom workflow combining scripts:

```bash
#!/bin/bash
# custom_workflow.sh

# Your custom steps
cd /Users/pavan/Work/CSULA-homegrownPAC

# 1. Fresh start
./scripts/fresh_start.sh

# 2. Run workflow
./scripts/run_workflow.sh

# 3. Generate emails
python3 scripts/send_emails.py --no-browser

# 4. Upload reports to cloud (example)
# rsync -avz output/scans/ user@server:/backup/

# 5. Send notification
echo "PDF scan complete!" | mail -s "Scan Results" admin@calstatela.edu
```

---

## WORKFLOW CHECKLIST

### Pre-Execution Checklist
- [ ] Python 3.9+ installed
- [ ] VeraPDF installed and in PATH
- [ ] `config.py` configured with correct domains
- [ ] Data files prepared (employees.csv, sites.csv)
- [ ] Scripts made executable (`chmod +x`)
- [ ] Database initialized
- [ ] Test domain configured for first run

### Execution Checklist
- [ ] Run `./scripts/fresh_start.sh`
- [ ] Verify backup created
- [ ] Run `./scripts/run_workflow.sh`
- [ ] Monitor progress (check logs)
- [ ] Verify reports generated in `output/scans/`
- [ ] Run `python3 scripts/send_emails.py`
- [ ] Review email content in browser
- [ ] Manually send emails via Outlook Web
- [ ] Run `python scripts/teams_upload.py` to copy reports to Teams
- [ ] Run `python scripts/historical_analysis.py` to update trend dashboards

### Post-Execution Checklist
- [ ] Verify all domains processed
- [ ] Check failure reports (if any)
- [ ] Reports uploaded to Teams (`python scripts/teams_upload.py`)
- [ ] Historical dashboards generated (`python scripts/historical_analysis.py`)
- [ ] Archive old reports (optional)
- [ ] Update domain configuration for next run
- [ ] Document any issues encountered

---

## QUICK REFERENCE COMMANDS

```bash
# Complete workflow from scratch
cd /Users/pavan/Work/CSULA-homegrownPAC
./scripts/fresh_start.sh && ./scripts/run_workflow.sh

# Check progress
./scripts/check_progress.sh

# Generate emails
python3 scripts/send_emails.py

# Upload reports to Teams (OneDrive)
python scripts/teams_upload.py

# Generate historical trend dashboards
python scripts/historical_analysis.py

# Historical dashboards - local output only (no upload)
python scripts/historical_analysis.py --no-upload

# View reports
open output/scans/

# Check database
sqlite3 drupal_pdfs.db "SELECT COUNT(*) FROM drupal_pdf_files;"
sqlite3 drupal_pdfs.db "SELECT COUNT(*) FROM pdf_report;"

# View logs
tail -f output/logs/pdf_checker.log

# Emergency stop
pkill -f "python3.*run_workflow"
```

---

## SCRIPT MODIFICATION

### Customize Fresh Start Behavior

Edit `scripts/fresh_start.sh`:

```bash
#!/bin/bash
# Add custom cleanup steps

# Example: Keep last 5 backups only
cd /Users/pavan/Work/CSULA-homegrownPAC
ls -t drupal_pdfs.db.backup.* | tail -n +6 | xargs rm -f

# Example: Archive old reports
tar -czf "output/backups/reports_$(date +%Y%m%d).tar.gz" output/scans/
```

### Customize Workflow Behavior

Edit `scripts/run_workflow.sh`:

```bash
#!/bin/bash
# Add custom steps

# Example: Send notification on completion
if [ $? -eq 0 ]; then
    echo "Workflow completed successfully" | mail -s "Success" admin@calstatela.edu
else
    echo "Workflow failed" | mail -s "Error" admin@calstatela.edu
fi
```

---

## SUPPORT & RESOURCES

### Documentation
- **Complete Setup Guide:** `setup/COMPLETE_SETUP_GUIDE.md`
- **Email Sending Guide:** `setup/EMAIL_SENDING_GUIDE.md`
- **Quick Reference:** `setup/QUICK_REFERENCE.md`
- **Project Structure:** `docs/PROJECT_STRUCTURE.md`

### Troubleshooting
- **Code Review Report:** `CODE_REVIEW_REPORT.md`
- **Improvements Document:** `IMPROVEMENTS.md`

### Contact
- **Email:** accessibility@calstatela.edu
- **Phone:** 323-343-6170 (ITS Help Desk)

---

**Last Updated:** November 3, 2025  
**Maintained By:** CSULA ITS / Accessibility Team  
**Version:** 1.0
