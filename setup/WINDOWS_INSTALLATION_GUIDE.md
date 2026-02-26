# CSULA HomegrownPAC - Windows Installation & Run Guide

Setup is fully automated. On a fresh machine, three commands are all you need.

> Email sending is **Windows-only** and uses **Outlook Desktop automation** (no SMTP).

---

## Prerequisites

- **Windows 10 / 11**
- **Git** -- to clone the repository (https://git-scm.com/)
- **Microsoft OneDrive** signed in to your Cal State LA account, with the Teams channel *"PDF Accessibility Checker (PAC) - General"* synced (so the folder appears in File Explorer under OneDrive). Required for the setup script to auto-detect the upload path.
- **Microsoft Outlook Desktop** installed and signed in -- required only when sending emails

Everything else (Python, Java, VeraPDF, the virtual environment, and all Python packages) is installed automatically by `setup.ps1`.

---

## First-Time Setup (New Machine)

### Step 1 - Clone the repository

```powershell
git clone https://github.com/pavanchauhan1604/CSULA-homegrownPAC.git
cd CSULA-homegrownPAC
```

### Step 2 - Allow PowerShell scripts (once per machine)

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Step 3 — Unblock scripts (ZIP download only)

If you downloaded the repo as a ZIP file instead of using `git clone`, Windows marks the files as coming from the internet and blocks them even after Step 2. Unblock them before running:

```powershell
Get-ChildItem -Recurse -Filter *.ps1 | Unblock-File
```

> This step is not needed if you used `git clone`.

### Step 4 — Run the setup script

```powershell
.\setup.ps1
```

`setup.ps1` automatically:
1. Installs **Python 3.11** via winget (if not already installed)
2. Installs **Java 21 Temurin JDK** via winget (required by VeraPDF)
3. Creates the `.venv` virtual environment inside the project folder
4. Installs all Python packages from `requirements.txt`
5. Creates all required `output/` and `temp/` subdirectories
6. Downloads and silently installs **VeraPDF** from the official GitHub releases
7. Writes the `VERAPDF_COMMAND` path into `config.py`
8. Auto-detects the synced OneDrive Teams channel folder and writes `TEAMS_ONEDRIVE_PATH` into `config.py`

> **Note:** If Python or Java were newly installed by the script (not already present), close the terminal, reopen it in the project root, and run `.\setup.ps1` again so the new PATH entries take effect. The script skips already-completed steps.

---

## Running the Workflow

All daily operations are run from the project root in PowerShell.

### Full pipeline (all 7 steps)

```powershell
.\scripts\run_workflow_smooth.ps1
```

Runs: setup DB, generate spiders, crawl sites, analyze PDFs, build Excel reports, generate email HTML, print summary.

### Send emails via Outlook Desktop

```powershell
# Interactive (prompts for confirmation)
.\scripts\send_emails.ps1

# Skip confirmation prompt
.\scripts\send_emails.ps1 -Force
```

Outlook Desktop must be signed in before running this.

### Check scan progress (while pipeline is running)

```powershell
.\scripts\check_progress.ps1
```

### Reset to a clean slate

```powershell
.\scripts\fresh_start.ps1
```

Backs up the database, then removes it along with all output files and generated spiders.

---

## Managing Domains

Domains are read from **`data/sites.csv`** -- no code changes needed.

To add or remove a domain, edit `data/sites.csv`:

```csv
https://www.calstatela.edu/admissions,CSULA-content-manager_pchauha5
https://www.calstatela.edu/financialaid,CSULA-content-manager_jsmith
```

Each row is a full `https://` URL followed by the site's security group name. The system converts these to internal domain keys automatically.

---

## Optional config.py Settings

`setup.ps1` writes `VERAPDF_COMMAND` and `TEAMS_ONEDRIVE_PATH` automatically. Other settings can be adjusted manually:

| Setting | Purpose |
|---|---|
| `TEST_EMAIL_RECIPIENT` | Email address for test/preview emails |
| `EMAIL_DRY_RUN` | `True` = generate emails but do not send |
| `OUTLOOK_DISPLAY_ONLY` | `True` = open drafts for review before sending |
| `OUTLOOK_SENT_ON_BEHALF_OF` | Set only if you have Exchange delegate permissions |
| `USE_TEST_DOMAINS_ONLY` | `True` = only scan `TEST_DOMAINS` (for development) |

---

## Troubleshooting

### "running scripts is disabled" in PowerShell
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Python or Java not found after running setup.ps1
Close the terminal, reopen it in the project root, and run `.\setup.ps1` again.

### VeraPDF not found / VERAPDF_COMMAND wrong
Re-run `.\setup.ps1` -- it will re-detect and rewrite the path. Or set it manually in `config.py`:
```python
VERAPDF_COMMAND = r"C:\Users\<you>\veraPDF\verapdf.bat"
```

### OneDrive path not detected
Make sure you are signed in to OneDrive with your Cal State LA account and that the *"PDF Accessibility Checker (PAC) - General"* Teams channel is synced (visible in File Explorer under OneDrive). Then re-run `.\setup.ps1`.

### Outlook sending errors
- Verify Outlook Desktop is open and signed in
- Verify the account has permission for `OUTLOOK_SENT_ON_BEHALF_OF` (if configured)
- Set `OUTLOOK_DISPLAY_ONLY = True` in `config.py` to open drafts interactively for debugging
