# CSULA PDF Checker - Quick Reference Card

## Setup (new machine)

```powershell
git clone https://github.com/pavanchauhan1604/CSULA-homegrownPAC.git
cd CSULA-homegrownPAC
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\setup.ps1
```

---

## Daily Workflow

```powershell
# Run the full pipeline
.\scripts\run_workflow_smooth.ps1

# Send emails via Outlook Desktop
.\scripts\send_emails.ps1 -Force

# Check scan progress (while pipeline is running)
.\scripts\check_progress.ps1

# Reset to clean slate (backs up DB, clears all outputs)
.\scripts\fresh_start.ps1
```

---

## Configuration

**File to edit:** `config.py`

```python
# Test email recipient
TEST_EMAIL_RECIPIENT = "your.email@calstatela.edu"

# Production mode (scan ALL domains from data/sites.csv)
USE_TEST_DOMAINS_ONLY = False
```

**To add or remove domains**, edit `data/sites.csv` (full URLs):
```csv
https://www.calstatela.edu/admissions,CSULA-content-manager_pchauha5
```

---

## Other Useful Commands

```powershell
# View current configuration
python -c "import config; config.print_config()"

# Open results in File Explorer
explorer .\output\scans
explorer .\output\emails

# Upload Excel reports to Teams via OneDrive
python scripts\teams_upload.py
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

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No such table" error | Run `.\scripts\run_workflow_smooth.ps1` (Step 0 creates the DB) |
| "verapdf: command not found" | Re-run `.\setup.ps1` to auto-install VeraPDF |
| Python / Java not in PATH | Close terminal, reopen, re-run `.\setup.ps1` |
| OneDrive path not detected | Sign in to OneDrive, sync the Teams channel, then re-run `.\setup.ps1` |
| Spiders already completed | Run `.\scripts\fresh_start.ps1` |
| SSL certificate errors | Already handled (SSL verification disabled) |
| Duplicate PDFs | Normal -- same PDF on different pages |

---

## Important Files

```
config.py                             # Central configuration (paths auto-written by setup.ps1)
data/sites.csv                        # Domain list (full URLs) -- edit here to add/remove domains
setup.ps1                             # One-time machine setup (Python, Java, VeraPDF, venv, packages)
scripts/run_workflow_smooth.ps1       # Full 7-step pipeline
scripts/send_emails.ps1               # Send emails via Outlook Desktop
scripts/check_progress.ps1            # Progress report with progress bar
scripts/fresh_start.ps1               # Clean reset (backs up DB, clears outputs)
output/scans/{domain}/*.xlsx          # Excel reports
output/emails/*.html                  # Email previews
drupal_pdfs.db                        # SQLite database (auto-generated)
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
