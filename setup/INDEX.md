# CSULA PDF Accessibility Checker - Documentation Index

**Last Updated:** February 2026

---

## What Do You Want to Do?

### Set up on a new machine
-> Read: **[WINDOWS_INSTALLATION_GUIDE.md](WINDOWS_INSTALLATION_GUIDE.md)**

Three steps: clone, allow scripts, run `.\setup.ps1`. Everything else is automated.

---

### Run the workflow / look up a command
-> Use: **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**

---

### Get a thorough overview of setup and operation
-> Read: **[COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)**

---

### Send emails after a scan
-> Read: **[EMAIL_SENDING_GUIDE.md](EMAIL_SENDING_GUIDE.md)**

---

## All Documentation Files

| File | Purpose |
|------|---------|
| **WINDOWS_INSTALLATION_GUIDE.md** | New machine setup (the main guide) |
| **QUICK_REFERENCE.md** | Daily command reference |
| **COMPLETE_SETUP_GUIDE.md** | Full setup and operation reference |
| **EMAIL_SENDING_GUIDE.md** | Email sending details |

---

## Quick Start (New Machine)

```powershell
git clone https://github.com/pavanchauhan1604/CSULA-homegrownPAC.git
cd CSULA-homegrownPAC
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\setup.ps1
```

Then:

```powershell
.\scripts\run_workflow_smooth.ps1
.\scripts\send_emails.ps1 -Force
```

---

## Key Files

| Path | Purpose |
|------|---------|
| `config.py` | Central configuration (paths auto-written by setup.ps1) |
| `data/sites.csv` | Domain list in full URL format -- edit to add/remove domains |
| `setup.ps1` | One-time machine setup script |
| `scripts/run_workflow_smooth.ps1` | Full pipeline |
| `scripts/send_emails.ps1` | Email sending |
| `scripts/check_progress.ps1` | Progress monitoring |
| `scripts/fresh_start.ps1` | Clean reset |
| `output/scans/{domain}/*.xlsx` | Excel reports |
| `output/emails/*.html` | Email previews |
| `drupal_pdfs.db` | SQLite database (auto-generated) |
