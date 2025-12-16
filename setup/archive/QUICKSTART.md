# Quick Start Guide - CSULA HomegrownPAC

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- Python 3.x installed
- VeraPDF CLI tool installed and in PATH
- SQLite (comes with Python)

### Step 1: Install Dependencies
```bash
pip install scrapy pikepdf pdfminer.six openpyxl jinja2 beautifulsoup4 requests lxml pywin32
```

### Step 2: Set Up Database
```bash
cd /Users/pavan/Work/CSULA-homegrownPAC
python src/core/database.py
```
This creates `drupal_pdfs.db` with all required tables.

### Step 3: Import Initial Data
```bash
# Edit data/employees.csv, data/sites.csv, data/site_assignments.csv with your data
python src/data_management/data_import.py
```

### Step 4: Run Your First Crawl
```bash
cd crawlers/sf_state_pdf_scan
python run_all_spiders.py
```
This will crawl all configured sites and save PDF URLs.

### Step 5: Test PDFs for Accessibility
```bash
cd /Users/pavan/Work/CSULA-homegrownPAC
python master_functions.py
```
In the Python console:
```python
>>> create_all_pdf_reports()
```

### Step 6: Generate Reports
```python
>>> build_all_xcel_reports()
```
Excel reports will be saved to `output/reports/`

### Step 7: Generate HTML Dashboard
```bash
python src/reporting/html_report.py
```

---

## 📋 Common Tasks

### Run a Single Site Scan
```python
from master_functions import build_single_xcel_report
build_single_xcel_report("example.csula.edu")
```

### Check for Broken Links (404s)
```python
from src.core.scan_refresh import refresh_status
refresh_status()
```

### Mark Removed PDFs
```python
from src.utilities.tools import mark_pdfs_as_removed
mark_pdfs_as_removed("/path/to/pdf_sites_folder")
```

### Generate and Send Emails
```python
from src.communication.communications import build_emails
emails = build_emails()

from src.communication.pdf_email import generate_email
for email_content, recipient in emails:
    generate_email(email_content, recipient)
```

### Query Database
```python
from src.data_management.data_export import get_all_sites, get_pdf_reports_by_site_name

# Get all sites
sites = get_all_sites()

# Get PDFs for a specific site
pdfs = get_pdf_reports_by_site_name("example.csula.edu")
```

---

## 🔧 Configuration

### Update Paths
The original code has hardcoded Windows paths. Update these in:

1. **master_functions.py**
   ```python
   pdf_sites_folder = "/path/to/your/pdf_scans"
   scans_output = "/path/to/your/output/{}"
   ```

2. **conformance_checker.py**
   ```python
   temp_pdf_path = "/Users/pavan/Work/CSULA-homegrownPAC/temp/temp.pdf"
   temp_profile_path = "/Users/pavan/Work/CSULA-homegrownPAC/temp/temp_profile.json"
   ```

3. **Spiders** (in `crawlers/sf_state_pdf_scan/sf_state_pdf_scan/spiders/*.py`)
   ```python
   output_folder = '/path/to/output/domain-name'
   ```

### Adjust Priority Thresholds
Edit `src/core/filters.py`:
```python
def is_high_priority(data):
    # Modify these conditions as needed
    if int(data['page_count']) > 0 and round(int(data['failed_checks']) / int(data['page_count'])) > 20:
        return True
    # ... add your custom logic
```

---

## 📊 Monthly Workflow

### Week 1: Crawling Phase
1. Update `data/sites.csv` with any new domains
2. Run all spiders: `python run_all_spiders.py`
3. Verify output in crawler folders

### Week 2: Testing Phase
1. Run `create_all_pdf_reports()` in master_functions.py
2. Monitor for errors in `failure` table
3. Re-run failed PDFs if needed

### Week 3: Reporting Phase
1. Generate Excel reports: `build_all_xcel_reports()`
2. Generate HTML dashboard: `python src/reporting/html_report.py`
3. Review reports for accuracy

### Week 4: Communication Phase
1. Generate emails: `build_emails()`
2. Review email content
3. Send emails to content managers

---

## 🐛 Troubleshooting

### VeraPDF Not Found
```bash
# Install VeraPDF and add to PATH
# Or update conformance_checker.py with full path:
verapdf_command = f'/full/path/to/verapdf -f ua1 --format json "{temp_pdf_path}" > "{temp_profile_path}"'
```

### Import Errors
```bash
# Make sure you're in the project root
cd /Users/pavan/Work/CSULA-homegrownPAC

# If you get ModuleNotFoundError, add project to PYTHONPATH:
export PYTHONPATH="${PYTHONPATH}:/Users/pavan/Work/CSULA-homegrownPAC"
```

### Database Locked
```python
# Close any open connections
conn.close()

# Or delete and recreate:
# rm drupal_pdfs.db
# python src/core/database.py
```

### Box.com PDFs Failing
Check `box_handler.py` - Box may have changed their HTML structure. Update the BeautifulSoup selectors if needed.

---

## 📚 Learn More

- **Full Documentation**: See `docs/` folder
- **ADA Guidelines**: See `docs/info/` folder
- **Project Structure**: See `docs/PROJECT_STRUCTURE.md`
- **SQL Queries**: See `sql/README.md`

---

## 🆘 Support

For issues or questions:
1. Check the README files in each folder
2. Review the info documentation in `docs/info/`
3. Contact the Accessibility Technology Initiative (ATI)

---

## ⚠️ Important Notes

- **Backup your database** before running full scans
- **Test with a single site** before processing all sites
- **Review Excel reports** before sending to stakeholders
- **Update paths** in the code to match your system
- **Monitor the `failure` table** for issues

---

Happy scanning! 🎉
