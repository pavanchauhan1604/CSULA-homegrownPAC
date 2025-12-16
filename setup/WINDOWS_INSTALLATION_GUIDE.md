# CSULA HomegrownPAC — Windows Installation & Run Guide

This guide walks you through a complete Windows setup (Python + dependencies + VeraPDF) and how to run the full workflow end-to-end.

> Email sending is **Windows-only** and uses **Outlook Desktop automation** (no SMTP).

---

## 1) Prerequisites (Windows)

- Windows 10/11
- Python **3.11+** (from python.org)
- Git (optional but recommended)
- **VeraPDF** desktop/CLI installed (required)
- **Microsoft Outlook Desktop** installed + signed in (required only for sending emails)

---

## 2) Install Python 3.11+

1. Download Python for Windows: https://www.python.org/downloads/windows/
2. Run the installer
3. Important:
   - ✅ Check **“Add python.exe to PATH”**
   - ✅ Check **“pip”**

Verify in PowerShell:

```powershell
python --version
python -m pip --version
```

---

## 3) Get the project

### Option A: Git clone (recommended)

```powershell
cd C:\Users\<you>\Work
git clone https://github.com/pavanchauhan1604/CSULA-homegrownPAC.git
cd CSULA-homegrownPAC
```

### Option B: Download ZIP

Download the repo ZIP from GitHub and extract it, then:

```powershell
cd C:\path\to\CSULA-homegrownPAC
```

---

## 4) Create and activate a virtual environment

In PowerShell, from the repo root:

```powershell
python -m venv .venv
```

If PowerShell blocks activation, run once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

---

## 5) Install Python dependencies

Install everything via `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

Quick verification:

```powershell
python -c "import scrapy, openpyxl, pikepdf, pandas, jinja2; print('Python deps OK')"
```

If you will send emails via Outlook automation, also verify:

```powershell
python -c "import win32com.client, pythoncom; print('pywin32 OK')"
```

---

## 6) Install VeraPDF (required)

1. Download VeraPDF for Windows: https://software.verapdf.org/
2. Run `verapdf-installer.exe`
3. Ensure VeraPDF is on PATH. If not, add it:
   - Control Panel → System → Advanced system settings → Environment Variables
   - Edit the **Path** variable
   - Add the VeraPDF install directory (commonly `C:\Program Files\veraPDF\`)

Verify:

```powershell
verapdf --version
```

If `verapdf` is not found, you can also set a full path in `config.py`:

- `VERAPDF_COMMAND = "C:\\Program Files\\veraPDF\\verapdf.bat"` (example)

---

## 7) Configure the project (`config.py`)

Edit `config.py` and set at least:

- `TEST_DOMAINS` (start with 1 domain)
- `USE_TEST_DOMAINS_ONLY = True` for first run
- `TEST_EMAIL_RECIPIENT` (for generating email previews)

Outlook sending options (Windows):

- `EMAIL_DRY_RUN` — if `True`, do not send (safe testing)
- `OUTLOOK_DISPLAY_ONLY` — if `True`, opens drafts for review instead of sending
- `OUTLOOK_SENT_ON_BEHALF_OF` — set only if you have permission to send on behalf of a mailbox

---

## 8) Run setup checks (recommended)

From repo root:

```powershell
python test_setup.py
```

This checks core prerequisites (including VeraPDF availability).

---

## 9) Run the full workflow (Windows)

> Note: the `.sh` workflow scripts are for macOS/Linux. On Windows, run the Python steps below.

### Step 0 — Setup database + test data

```powershell
python scripts\setup_test_environment.py
```

### Step 1 — Generate spiders

```powershell
python config\generate_spiders.py
```

### Step 2 — Crawl sites to discover PDFs

```powershell
cd crawlers\sf_state_pdf_scan
python run_all_spiders.py
cd ..\..\
```

### Step 3 — Analyze PDFs with VeraPDF (build DB reports)

```powershell
python master_functions.py
```

### Step 4 — Generate Excel reports

```powershell
python -c "from master_functions import build_all_xcel_reports; build_all_xcel_reports()"
```

### Step 5 — Generate email HTML previews

```powershell
python scripts\generate_emails.py
```

Outputs:
- Excel reports: `output\scans\...\*.xlsx`
- Email previews: `output\emails\*.html`

---

## 10) Send emails (Windows + Outlook Desktop)

1. Ensure Outlook Desktop is installed and you can send mail normally.
2. Keep Outlook open (recommended for first run).
3. From repo root:

```powershell
python scripts\send_emails.py
```

Tips:
- Set `EMAIL_DRY_RUN = True` first to validate generation without sending.
- Set `OUTLOOK_DISPLAY_ONLY = True` to review drafts before sending.

---

## Troubleshooting (Windows)

### PowerShell: “running scripts is disabled”
Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### `verapdf` not found
- Confirm it’s installed
- Confirm PATH contains the VeraPDF directory
- Or set `VERAPDF_COMMAND` to the full path in `config.py`

### Outlook sending errors
- Verify Outlook Desktop is signed in
- Verify the account has permission for `OUTLOOK_SENT_ON_BEHALF_OF` (if used)
- Try `OUTLOOK_DISPLAY_ONLY = True` to debug drafts interactively
