# 🚀 Quick Start - Run Your First Scan

## Current Status: ✅ Almost Ready!

Your setup test results:
- ✅ Configuration: Working
- ✅ Database: 3 domains ready (calstatela.edu, www-adminfin.calstatela.edu, academicsenate.calstatela.edu)
- ✅ Your email configured: pchauha5@calstatela.edu
- ⚠️ VeraPDF: **Needs Installation**
- ✅ Output directories: Ready
- ✅ Spiders: Framework ready

---

## STEP 1: Install VeraPDF (Required)

VeraPDF validates PDF accessibility. Choose one method:

### Option A: Homebrew (Recommended for macOS)
```bash
brew install verapdf
```

### Option B: Direct Download
1. Visit: https://verapdf.org/home/
2. Download the installer for macOS
3. Install and add to PATH

### Verify Installation
```bash
verapdf --version
# Should show version info
```

---

## STEP 2: Generate Spiders for Your Domains

This creates web crawlers for each of your test domains:

```bash
cd /Users/pavan/Work/CSULA-homegrownPAC/crawlers/sf_state_pdf_scan
python3 ../../config/sites.py
```

**What this does:**
- Reads domains from database
- Creates one spider per domain
- Spiders are saved to: `sf_state_pdf_scan/spiders/`

**Expected output:**
```
Generated spider for calstatela.edu: calstatela_spider.py
Generated spider for www-adminfin.calstatela.edu: www_adminfin_calstatela_spider.py
Generated spider for academicsenate.calstatela.edu: academicsenate_spider.py
```

---

## STEP 3: Run Spiders to Find PDFs

Now crawl the websites to find all PDF files:

```bash
# Still in crawlers/sf_state_pdf_scan directory
python3 run_all_spiders.py
```

**What this does:**
- Crawls each domain
- Follows all internal links
- Identifies PDF files
- Saves results to `output/scans/{domain}/scanned_pdfs.txt`

**How long:** 5-15 minutes depending on site size

**Check progress:**
```bash
# In another terminal
tail -f /Users/pavan/Work/CSULA-homegrownPAC/output/scans/calstatela-edu/scanned_pdfs.txt
```

---

## STEP 4: Analyze PDFs for Accessibility

Download and check each PDF for accessibility issues:

```bash
cd /Users/pavan/Work/CSULA-homegrownPAC

# Method 1: Use master_functions (recommended)
python3 -c "
import sys
sys.path.insert(0, 'src/core')
sys.path.insert(0, 'src/data_management')
sys.path.insert(0, 'src/utilities')

from master_functions import create_all_pdf_reports
create_all_pdf_reports()
"

# OR Method 2: Step by step
python3 -c "
import sys, os
sys.path.insert(0, 'src/core')
sys.path.insert(0, 'src/data_management')
sys.path.insert(0, 'src/utilities')
os.chdir('src/core')

from conformance_checker import full_pdf_scan
from scan_refresh import refresh_status
from tools import mark_pdfs_as_removed
import config

full_pdf_scan(str(config.PDF_SITES_FOLDER))
refresh_status()
mark_pdfs_as_removed(str(config.PDF_SITES_FOLDER))
"
```

**What this does:**
- Downloads each PDF
- Runs VeraPDF validation
- Counts accessibility violations
- Checks metadata (title, language, tags)
- Stores results in database

**How long:** 30-60 minutes for ~150 PDFs

---

## STEP 5: Generate Excel Reports

Create Excel spreadsheets with all findings:

```bash
python3 -c "
import sys
sys.path.insert(0, 'src/data_management')
sys.path.insert(0, 'src/core')
import config

from data_export import get_all_sites, get_pdf_reports_by_site_name, write_data_to_excel, get_site_failures
from master_functions import build_all_xcel_reports

build_all_xcel_reports()
"
```

**Reports will be at:**
- `output/scans/calstatela-edu/calstatela-pdf-scans.xlsx`
- `output/scans/www-adminfin-calstatela-edu/www-adminfin-pdf-scans.xlsx`
- `output/scans/academicsenate-calstatela-edu/academicsenate-pdf-scans.xlsx`

---

## STEP 6: Generate Email Reports

Create HTML emails summarizing findings for each user:

```bash
python3 -c "
import sys
sys.path.insert(0, 'src/communication')

from communications import build_emails
import config

emails = build_emails()

# Save to files
import os
os.makedirs('output/emails', exist_ok=True)
for email_html, recipient in emails:
    filename = f'output/emails/email_{recipient.replace(\"@\", \"_at_\").replace(\".\", \"_\")}.html'
    with open(filename, 'w') as f:
        f.write(email_html)
    print(f'Saved: {filename}')
"
```

**Your email report:** `output/emails/email_pchauha5_at_calstatela_edu.html`

**View it:**
```bash
open output/emails/email_pchauha5_at_calstatela_edu.html
```

---

## STEP 7: Check Results

### View Database Summary
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('drupal_pdfs.db')
c = conn.cursor()

print('📊 Results Summary')
print('='*60)

c.execute('SELECT COUNT(*) FROM drupal_pdf_files')
print(f'Total PDFs found: {c.fetchone()[0]}')

c.execute('SELECT COUNT(*) FROM pdf_report')
print(f'PDFs analyzed: {c.fetchone()[0]}')

c.execute('SELECT COUNT(*) FROM pdf_report WHERE violations > 0')
print(f'PDFs with violations: {c.fetchone()[0]}')

c.execute('SELECT AVG(violations) FROM pdf_report WHERE violations > 0')
avg = c.fetchone()[0]
print(f'Average violations: {avg:.1f}' if avg else 'Average violations: 0')

print('\\nBy Domain:')
c.execute('''
    SELECT ds.domain_name, COUNT(dpf.id), 
           COUNT(CASE WHEN pr.violations > 0 THEN 1 END)
    FROM drupal_site ds
    LEFT JOIN drupal_pdf_files dpf ON ds.id = dpf.drupal_site_id
    LEFT JOIN pdf_report pr ON dpf.file_hash = pr.pdf_hash
    GROUP BY ds.domain_name
''')
for domain, total, with_violations in c.fetchall():
    print(f'  {domain}: {total} PDFs, {with_violations} with issues')

conn.close()
"
```

### View Excel Reports
```bash
ls -lh output/scans/*/*.xlsx
```

### View Email Reports
```bash
ls -lh output/emails/
```

---

## ONE-COMMAND RUN (After VeraPDF is installed)

Once VeraPDF is installed, you can run everything in sequence:

```bash
cd /Users/pavan/Work/CSULA-homegrownPAC

# Complete workflow
(
  echo "🔄 Step 1: Generate spiders..."
  cd crawlers/sf_state_pdf_scan && python3 ../../config/sites.py
  
  echo "🔄 Step 2: Crawl websites..."
  python3 run_all_spiders.py
  
  echo "🔄 Step 3: Analyze PDFs..."
  cd ../.. && python3 master_functions.py
  
  echo "🔄 Step 4: Generate reports..."
  python3 -c "from master_functions import build_all_xcel_reports; build_all_xcel_reports()"
  
  echo "✅ Workflow complete!"
  echo "📊 Check output/scans/ for Excel reports"
  echo "📧 Check output/emails/ for email reports"
)
```

---

## Troubleshooting

### If spiders don't generate
```bash
# Check database has domains
python3 -c "
import sqlite3
conn = sqlite3.connect('drupal_pdfs.db')
c = conn.cursor()
c.execute('SELECT domain_name FROM drupal_site')
for row in c.fetchall():
    print(row[0])
"
```

### If PDF analysis fails
```bash
# Check temp directory
ls -lh temp/

# Check VeraPDF works
verapdf --help

# Check a PDF manually
verapdf -f ua1 --format json temp/temp.pdf
```

### If reports are empty
```bash
# Check if PDFs were found
cat output/scans/calstatela-edu/scanned_pdfs.txt | wc -l

# Check database
sqlite3 drupal_pdfs.db "SELECT COUNT(*) FROM drupal_pdf_files;"
```

### If you need to start over
```bash
# Delete database and start fresh
rm drupal_pdfs.db
python3 setup_test_environment.py

# Or just clear PDF data
sqlite3 drupal_pdfs.db "DELETE FROM drupal_pdf_files; DELETE FROM pdf_report; DELETE FROM failure;"
```

---

## Expected Timeline

For 3 domains with ~50 PDFs each:

| Step | Time | What's Happening |
|------|------|------------------|
| Spider Generation | 1-2 min | Creating crawler code |
| Web Crawling | 5-10 min | Finding PDF links |
| PDF Analysis | 30-45 min | Downloading & validating PDFs |
| Report Generation | 2-5 min | Creating Excel & HTML reports |
| **Total** | **40-60 min** | **Complete workflow** |

---

## What to Expect in Results

### Excel Report Contains:
- PDF URL and location
- Accessibility violations count
- Specific failed checks
- Metadata status (title, language)
- Tagged status
- Page count
- High priority flags

### Email Report Shows:
- Summary table by domain
- Total PDFs vs. high priority issues
- Links to detailed reports
- Your assigned sites only

### Database Contains:
- All PDF URLs and metadata
- Detailed violation reports
- Site assignments
- Error logs

---

## Next Steps After First Run

1. **Review Excel reports** - Look at the violations
2. **Check email preview** - See what users will receive
3. **Query database** - Get specific statistics
4. **Adjust priorities** - Configure in `config/priority_profiles.py`
5. **Add more domains** - Edit `data/sites.csv` and re-run setup
6. **Schedule regular scans** - Set up cron job or scheduled task

---

## Getting Help

- **Detailed workflow:** See `RUN_WORKFLOW.md`
- **Configuration:** See `CONFIG_SETUP.md` and `CONFIG_QUICK_REFERENCE.md`
- **Project structure:** See `docs/PROJECT_STRUCTURE.md`
- **Test setup:** Run `python3 test_setup.py`

---

## Summary Commands

```bash
# 1. Install VeraPDF
brew install verapdf

# 2. Run test
python3 test_setup.py

# 3. Start workflow
cd crawlers/sf_state_pdf_scan
python3 ../../config/sites.py
python3 run_all_spiders.py
cd ../..
python3 master_functions.py

# 4. View results
open output/scans/*/  *.xlsx
open output/emails/*.html
```

**You're ready to go! Start with Step 1 (Install VeraPDF).** 🚀
