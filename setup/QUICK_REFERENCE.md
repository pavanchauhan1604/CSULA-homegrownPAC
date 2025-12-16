# CSULA PDF Checker - Quick Reference Card

## 🚀 Quick Start

```bash
# macOS/Linux: complete fresh run (recommended for first time)
cd /path/to/CSULA-homegrownPAC
./scripts/fresh_start.sh && ./scripts/run_workflow.sh
```

**Windows (PowerShell):** follow the step-by-step workflow in `setup/WINDOWS_INSTALLATION_GUIDE.md`.

---

## ⚙️ Configuration

**File to edit:** `config.py`

```python
# Change your test domains
TEST_DOMAINS = [
    "calstatela.edu",
]

# Change test email
TEST_EMAIL_RECIPIENT = "your.email@calstatela.edu"

# Production mode (scans ALL domains)
USE_TEST_DOMAINS_ONLY = False  # Set to False for production
```

---

## 📝 Common Commands

```bash
# Clean everything and restart
./scripts/fresh_start.sh

# Run complete workflow
./scripts/run_workflow.sh

# Check progress while running
./scripts/check_progress.sh

# View configuration
python3 -c "import config; config.print_config()"

# Open results
open output/scans/*/*.xlsx        # Excel reports
open output/emails/*.html         # Email previews

# Database queries
sqlite3 drupal_pdfs.db            # Open database
```

**Windows (PowerShell) equivalents:**

```powershell
# View configuration
python -c "import config; config.print_config()"

# Generate email previews (HTML)
python scripts\generate_emails.py

# Send emails (Windows + Outlook Desktop)
python scripts\send_emails.py

# Open outputs in File Explorer
explorer .\output\scans
explorer .\output\emails
```

---

## 📊 Database Queries

```sql
-- Count total PDFs
SELECT COUNT(*) FROM drupal_pdf_files;

-- Count unique PDFs
SELECT COUNT(DISTINCT pdf_uri) FROM drupal_pdf_files;

-- Count analyzed PDFs
SELECT COUNT(*) FROM pdf_report;

-- PDFs with most violations
SELECT pdf_hash, violations 
FROM pdf_report 
ORDER BY violations DESC 
LIMIT 10;

-- Domain statistics
SELECT 
    s.domain_name, 
    COUNT(p.id) as pdf_count 
FROM drupal_site s 
LEFT JOIN drupal_pdf_files p ON s.id = p.drupal_site_id 
GROUP BY s.domain_name;
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No such table" error | Run `python3 scripts/setup_test_environment.py` |
| "verapdf: command not found" | Install VeraPDF and ensure it is in PATH (Windows installer: https://software.verapdf.org/) |
| Spiders already completed | Run `./scripts/fresh_start.sh` |
| SSL certificate errors | Already handled (SSL verification disabled) |
| Duplicate PDFs | Normal - same PDF on different pages |

---

## 📁 Important Files

```
config.py                        # EDIT THIS for configuration
scripts/run_workflow.sh          # Complete workflow
scripts/fresh_start.sh           # Clean and reset
scripts/check_progress.sh        # Monitor progress
output/scans/{domain}/*.xlsx     # Excel reports
output/emails/*.html             # Email previews
drupal_pdfs.db                   # Database
```

---

## ⏱️ Typical Runtime

- **Setup:** 1 minute
- **Web crawl:** 5-15 minutes per domain
- **PDF analysis:** 30-60 minutes (depends on PDF count)
- **Report generation:** 1-2 minutes
- **Total (1 domain):** ~45-90 minutes

---

## 📈 Expected Results

- **PDFs found:** 100-1000+ per domain
- **Unique PDFs:** 10-20% of total (many duplicates)
- **Violation rate:** 90-95% of PDFs
- **Avg violations:** 4-6 per PDF

---

## 📧 Email Report Contents

- Domain name
- Total PDFs found
- PDFs needing attention
- Clickable links to review PDFs
- Cal State LA branding

---

## 🎯 Production Checklist

- [ ] VeraPDF installed (`verapdf --version`)
- [ ] Python packages installed
- [ ] `config.py` configured with your domains
- [ ] Test run completed successfully
- [ ] Excel reports reviewed
- [ ] Email templates reviewed
- [ ] Ready to add more domains

---

For complete documentation, see: `setup/COMPLETE_SETUP_GUIDE.md`
