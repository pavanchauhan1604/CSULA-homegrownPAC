# Running the CSULA PDF Accessibility Checker Workflow

## Complete Workflow Steps

### Prerequisites Check

Before running, ensure you have:

```bash
# 1. Check Python version (3.7+)
python3 --version

# 2. Check VeraPDF is installed
verapdf --version
# If not installed: https://verapdf.org/home/

# 3. Verify database exists
ls -lh drupal_pdfs.db

# 4. Check configuration
python3 config.py
```

---

## PHASE 1: Generate Web Crawlers (Spiders)

The first step is to generate Scrapy spiders for each domain in your test list.

### Step 1.1: Update Spider Generator

Since we're using the new config system, we need to update `config/sites.py` to use config paths. For now, let's use it as-is but be aware it has hardcoded paths.

```bash
cd /Users/pavan/Work/CSULA-homegrownPAC
```

### Step 1.2: Generate Spiders for Test Domains

**Option A: Generate for all domains in database**
```bash
cd crawlers/sf_state_pdf_scan
python3 ../../config/sites.py
```

**Option B: Manually check what domains will be processed**
```bash
python3 -c "
import sys
sys.path.insert(0, 'src/data_management')
from data_import import get_all_sites_domain_names

domains = get_all_sites_domain_names()
print('Domains to scan:')
for d in domains:
    print(f'  - {d}')
"
```

**Note:** The spider generator (`config/sites.py`) will create one spider per domain in:
`crawlers/sf_state_pdf_scan/sf_state_pdf_scan/spiders/`

---

## PHASE 2: Run Web Crawlers to Find PDFs

Now we'll run the spiders to crawl each website and find all PDF links.

### Step 2.1: Run All Spiders

```bash
cd /Users/pavan/Work/CSULA-homegrownPAC/crawlers/sf_state_pdf_scan

# Run all spiders
python3 run_all_spiders.py
```

This will:
- Crawl each domain
- Find all PDF links
- Find Box.com shared files (if any)
- Save results to `output/scans/{domain-name}/scanned_pdfs.txt`

**Expected Output:**
- One folder per domain in `output/scans/`
- Each folder contains `scanned_pdfs.txt` with format: `PDF_URL PARENT_URL TIMESTAMP`

### Step 2.2: Verify Spider Output

```bash
# Check what was found
ls -lh output/scans/

# View PDFs found for a specific domain
cat output/scans/calstatela-edu/scanned_pdfs.txt | head -10
```

---

## PHASE 3: Download and Analyze PDFs

Now we'll download each PDF and run accessibility checks using VeraPDF.

### Step 3.1: Update Import Paths

First, we need to ensure the Python modules can be imported. Add the project root to Python path:

```bash
export PYTHONPATH="/Users/pavan/Work/CSULA-homegrownPAC:$PYTHONPATH"
```

### Step 3.2: Run Full PDF Scan

**Option A: Scan all domains**
```bash
cd /Users/pavan/Work/CSULA-homegrownPAC

python3 -c "
import sys
sys.path.insert(0, 'src/core')
sys.path.insert(0, 'src/data_management')

from conformance_checker import full_pdf_scan
from scan_refresh import refresh_status
from utilities.tools import mark_pdfs_as_removed

# Path to spider output
pdf_sites_folder = 'output/scans'

print('Step 1: Scanning PDFs and creating reports...')
full_pdf_scan(pdf_sites_folder)

print('Step 2: Checking for 404s...')
refresh_status()

print('Step 3: Marking removed PDFs...')
mark_pdfs_as_removed(pdf_sites_folder)

print('✅ PDF scan complete!')
"
```

**Option B: Scan single domain (safer for testing)**
```bash
python3 -c "
import sys
sys.path.insert(0, 'src/core')
sys.path.insert(0, 'src/data_management')

from conformance_checker import single_site_pdf_scan
from scan_refresh import refresh_status

site_folder = 'output/scans/calstatela-edu'

print('Scanning single site...')
single_site_pdf_scan(site_folder)

print('Checking status...')
refresh_status(site='calstatela.edu')

print('✅ Single site scan complete!')
"
```

This will:
- Download each PDF
- Run VeraPDF accessibility validation
- Parse violations and create reports
- Store results in database
- Check for 404 errors

---

## PHASE 4: Generate Excel Reports

Create Excel reports with all PDF accessibility data.

### Step 4.1: Generate Report for Test Domains

```bash
python3 -c "
import sys
sys.path.insert(0, 'src/data_management')
sys.path.insert(0, 'src/core')

from data_export import get_all_sites, get_pdf_reports_by_site_name, write_data_to_excel, get_site_failures
import os
from datetime import datetime

output_base = 'output/scans'

sites = get_all_sites()
print(f'Generating Excel reports for {len(sites)} sites...')

for site in sites:
    site_folder = site.replace('.', '-')
    site_data = get_pdf_reports_by_site_name(site)
    fail_data = get_site_failures(site)
    
    output_folder = f'{output_base}/{site_folder}'
    os.makedirs(output_folder, exist_ok=True)
    
    # Create backup folder
    backup_folder = f'{output_folder}/backups'
    os.makedirs(backup_folder, exist_ok=True)
    
    # Move old file if exists
    report_file = f'{output_folder}/{site_folder.split(\"-\")[0]}-pdf-scans.xlsx'
    if os.path.exists(report_file):
        backup_file = f'{backup_folder}/{site_folder.split(\"-\")[0]}-pdf-scans-backup-{datetime.now().strftime(\"%Y-%m-%d\")}.xlsx'
        os.rename(report_file, backup_file)
        print(f'  Backed up old report: {backup_file}')
    
    # Generate new report
    write_data_to_excel(site_data, fail_data, report_file)
    print(f'✅ Generated: {report_file}')

print('All Excel reports generated!')
"
```

---

## PHASE 5: Generate Email Reports

Generate HTML email summaries for each user.

### Step 5.1: Build Email Reports

```bash
python3 -c "
import sys
sys.path.insert(0, 'src/communication')

from communications import build_emails

print('Building email reports...')
emails = build_emails()

print(f'✅ Generated {len(emails)} email reports')
for i, (email_html, recipient) in enumerate(emails[:3]):  # Show first 3
    print(f'  Email {i+1} for: {recipient}')
    
# Optionally save emails to files for review
import os
os.makedirs('output/emails', exist_ok=True)
for i, (email_html, recipient) in enumerate(emails):
    filename = f'output/emails/email_{recipient.replace(\"@\", \"_\")}.html'
    with open(filename, 'w') as f:
        f.write(email_html)
    print(f'Saved: {filename}')
"
```

### Step 5.2: Review Email (Before Sending)

```bash
# Open an email in browser to review
open output/emails/email_pchauha5_calstatela.edu.html
```

---

## PHASE 6: Send Emails (Optional)

**Email sending is Windows-only** in this project.

- On Windows: run `python3 scripts/send_emails.py` (requires Outlook Desktop + pywin32).
- On macOS: use the saved HTML files under `output/emails/` and send manually.

---

## PHASE 7: Generate Monthly HTML Report

Create a comprehensive HTML report summarizing all findings.

```bash
python3 -c "
import sys
sys.path.insert(0, 'src/reporting')
sys.path.insert(0, 'src/data_management')

# The html_report.py module would generate the monthly report
# This needs to be reviewed and potentially updated

print('Monthly report generation - see src/reporting/html_report.py')
"
```

---

## Complete Workflow Script

Here's a complete script that runs everything:

```bash
#!/bin/bash
# complete_workflow.sh

set -e  # Exit on error

echo "=========================================="
echo "CSULA PDF Accessibility Checker"
echo "Complete Workflow"
echo "=========================================="

# Setup
cd /Users/pavan/Work/CSULA-homegrownPAC
export PYTHONPATH="$PWD:$PYTHONPATH"

echo ""
echo "Phase 1: Generate Spiders"
echo "=========================================="
cd crawlers/sf_state_pdf_scan
python3 ../../config/sites.py
cd ../..

echo ""
echo "Phase 2: Crawl Websites for PDFs"
echo "=========================================="
cd crawlers/sf_state_pdf_scan
python3 run_all_spiders.py
cd ../..

echo ""
echo "Phase 3: Analyze PDFs"
echo "=========================================="
python3 master_functions.py

echo ""
echo "Phase 4: Generate Reports"
echo "=========================================="
# Run report generation code here

echo ""
echo "✅ Workflow Complete!"
echo "Check output/scans/ for results"
```

Save this as `complete_workflow.sh` and run:
```bash
chmod +x complete_workflow.sh
./complete_workflow.sh
```

---

## Simplified Test Run (Recommended First Step)

For your first test, try this simplified approach:

```bash
# 1. Verify setup
python3 config.py

# 2. Check database
python3 -c "
import sqlite3
conn = sqlite3.connect('drupal_pdfs.db')
cursor = conn.cursor()
cursor.execute('SELECT domain_name FROM drupal_site')
print('Test domains:')
for row in cursor.fetchall():
    print(f'  - {row[0]}')
"

# 3. Generate ONE spider for testing
python3 -c "
# This would generate a spider for just one domain
# See config/sites.py for the full implementation
print('See config/sites.py to generate spiders')
"

# 4. Run ONE spider manually
cd crawlers/sf_state_pdf_scan
scrapy list  # Shows available spiders
scrapy crawl <spider_name>  # Run specific spider

# 5. Check results
ls -lh ../../output/scans/
```

---

## Monitoring Progress

### Check Database Contents

```bash
# View all PDFs found
sqlite3 drupal_pdfs.db "SELECT COUNT(*) FROM drupal_pdf_files;"

# View reports generated
sqlite3 drupal_pdfs.db "SELECT COUNT(*) FROM pdf_report;"

# View failures
sqlite3 drupal_pdfs.db "SELECT * FROM failure ORDER BY error_date DESC LIMIT 5;"
```

### Check Output Files

```bash
# Spider outputs
ls -lh output/scans/*/scanned_pdfs.txt

# Excel reports
ls -lh output/scans/*/*.xlsx

# Email reports
ls -lh output/emails/
```

---

## Troubleshooting

### Issue: Module Import Errors

```bash
# Add project to Python path
export PYTHONPATH="/Users/pavan/Work/CSULA-homegrownPAC:$PYTHONPATH"

# Or run from project root
cd /Users/pavan/Work/CSULA-homegrownPAC
```

### Issue: VeraPDF Not Found

```bash
# Install VeraPDF
brew install verapdf  # macOS with Homebrew
# Or download from https://verapdf.org/

# Verify installation
verapdf --version
```

### Issue: Database Locked

```bash
# Close any open connections
# Or restart Python process
```

### Issue: Permission Denied

```bash
# Make output directories writable
chmod -R 755 output/
```

---

## Expected Timeline

For 3 test domains with ~50 PDFs each:

1. Spider generation: 1-2 minutes
2. Web crawling: 5-10 minutes  
3. PDF analysis: 15-30 minutes (depends on PDF count)
4. Report generation: 2-5 minutes

**Total: ~30-45 minutes**

---

## Next Steps After First Run

1. Review Excel reports in `output/scans/`
2. Check email HTML files in `output/emails/`
3. Verify data in database with SQL queries
4. Adjust configuration if needed
5. Scale up to more domains

---

## Important Notes

⚠️ **Current Limitations:**
- Some modules still have hardcoded paths (need updating)
- Email sending requires Windows + Outlook Desktop (Outlook automation)
- Box.com integration may need authentication
- Large domain scans can take hours

✅ **What's Working:**
- Configuration system
- Database setup
- Spider generation framework
- PDF download and analysis logic
- Excel report generation
- HTML email generation

🔧 **Needs Manual Configuration:**
- Update import statements in modules to use config
- Configure Outlook Desktop (Windows) for email sending
- Adjust crawling speed if needed
- Set up Box.com credentials if using Box storage
