# CLAUDE.md — CSULA HomegrownPAC

## Project Purpose
Automated PDF accessibility compliance system for Cal State LA (CSULA).
Crawls university websites, tests PDFs against PDF/UA 1.0 via VeraPDF, generates
Excel reports, syncs to SharePoint/Teams via OneDrive, and sends personalised
emails to content managers via Outlook COM (Windows-only).

**ADA Title II compliance deadline: April 24, 2026.**

---

## Tech Stack
Python 3.11+, SQLite (drupal_pdfs.db), Scrapy, VeraPDF, openpyxl, pikepdf,
pdfminer.six, Chart.js (HTML dashboards), Outlook COM / pywin32 (Windows only).
All paths/settings are centralised in `config.py` — never hardcode paths elsewhere.

---

## End-to-End Data Pipeline

```
data/sites.csv  →  Scrapy spiders crawl domains
                →  output/scans/{domain}/scanned_pdfs.txt   (PDF URL list)
                →  conformance_checker.py: download + VeraPDF + pikepdf analysis
                →  drupal_pdfs.db  (SQLite)
                →  write_data_to_excel() → {domain}-YYYY-MM-DD_HH-MM-SS.xlsx
                →  sharepoint_sync.py: copy Excel to OneDrive/{domain}/
                                       write HTML drafts to {domain}/Mail Drafts/
                →  send_emails.py: read drafts, attach Excel, send via Outlook COM
                →  generate_master_report.py      → Master/Master Report.xlsx
                   generate_master_report_html.py → Master/master_report.html
                   historical_analysis.py         → {domain}/historical_analysis.html
```

---

## Key Files

| File | Purpose |
|---|---|
| `config.py` | Single source of truth for ALL paths, settings, domain list |
| `src/core/database.py` | SQLite schema (6 tables) |
| `src/core/conformance_checker.py` | PDF downloading, VeraPDF execution, full scan |
| `src/core/pdf_priority.py` | pikepdf/pdfminer analysis: tagging, metadata, text type |
| `src/core/filters.py` | `is_high_priority()`, `get_priority_level()` |
| `src/data_management/data_import.py` | CSV → DB imports (employees, sites, assignments) |
| `src/data_management/data_export.py` | SQL → Excel generation (multi-sheet workbook) |
| `src/communication/communications.py` | HTML email content generation |
| `src/communication/outlook_sender.py` | Outlook COM email sending (Windows) |
| `scripts/sharepoint_sync.py` | OneDrive sync + per-employee HTML draft generation |
| `scripts/send_emails.py` | Read drafts → send via Outlook |
| `scripts/generate_master_report.py` | Master Excel (Data/Dashboard/Run Index sheets) |
| `scripts/generate_master_report_html.py` | Master HTML dashboard with Chart.js |
| `scripts/historical_analysis.py` | Per-domain HTML trend dashboards |
| `crawlers/sf_state_pdf_scan/run_all_spiders.py` | Spider orchestration (restart-safe) |

---

## Naming Conventions — CRITICAL

Domains appear in four different forms throughout the codebase:

| Context | Format | Example |
|---|---|---|
| Database / internal key | dots + underscores | `www.calstatela.edu_admissions` |
| OneDrive folder name | all hyphens | `www-calstatela-edu-admissions` |
| Human display (emails) | dots + slashes | `www.calstatela.edu/admissions` |
| URL input | full URL | `https://www.calstatela.edu/admissions` |

**Conversion functions in config.py:**
- `_url_to_domain_key(url)` → internal key (underscores)
- `get_domain_folder_name(key)` → OneDrive folder name (hyphens)
- `normalize_domain_key(key)` → strips www, https://
- `_display_domain(key)` (in communications.py) → human display (slashes)

**Excel filename format:** `{domain_key}-{YYYY-MM-DD_HH-MM-SS}.xlsx`
**Timestamp regex:** `(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.xlsx$`
**Config constant:** `EXCEL_REPORT_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"`

---

## OneDrive Folder Structure

```
{TEAMS_ONEDRIVE_PATH}/                   ← config.TEAMS_ONEDRIVE_PATH
├── www-calstatela-edu-admissions/
│   ├── www.calstatela.edu_admissions-2026-01-25_06-26-57.xlsx   ← timestamped reports accumulate
│   ├── historical_analysis.html          ← overwritten each run
│   └── Mail Drafts/
│       ├── pchauha5_draft.html           ← overwritten each run
│       └── jsmith_draft.html
├── libguides-calstatela-edu/
│   └── ...
└── Master/                              ← always write here, never in root
    ├── Master Report.xlsx               ← Data sheet accumulates; Dashboard refreshed
    └── master_report.html               ← fully overwritten each run
```

The `Master/` subfolder is created automatically. Both master report scripts must
always write there — never to the OneDrive root directly.

---

## Excel Report Structure (per-domain)

**Sheet: Unique PDFs** — deduplicated by `file_hash` (SHA-256); one row per actual PDF file.
This is the primary sheet read by all reporting/master scripts.

**Sheet: Scanned PDFs** — one row per PDF occurrence (same file on multiple pages = multiple rows).

**Key columns present in both sheets:**

| Column | Description |
|---|---|
| `pdf_uri` | Hyperlinked PDF URL |
| `parent_uri` | Hyperlinked page containing the PDF |
| `violations` | VeraPDF PDF/UA 1.0 violation count |
| `failed_checks` | Count of failed accessibility checks |
| `tagged` | 1/0 — structurally tagged |
| `pdf_text_type` | "Text Only" / "Image Only" / "Image Over Text" / "No Image or Text" |
| `page_count` | Total pages |
| `has_form` | 1/0 — contains form fields |
| `approved_pdf_exporter` | 1/0 — created by approved tool (e.g. Equidox 7) |
| `Errors/Page` | Computed: `violations / page_count` |
| `Low Priority` | User-editable dropdown: Yes / No |
| `fingerprint` | SHA-256 hash (renamed from `file_hash`) |

**High-priority rows** get red fill. `Low Priority = "No"` → high priority; `"Yes"` → low/safe.

**Other sheets:** Grouped by PDF URL, Grouped by Parent URL, Failure, Instructions.

---

## Priority System

### `is_high_priority(data)` → bool (`src/core/filters.py`)
Returns `True` (requires urgent attention) if ANY:
- `tagged == 0` (untagged PDF)
- `pdf_text_type == "Image Only"` (no extractable text)
- `violations_per_page > 20`
- `has_form == 1` AND `violations_per_page > 3`

Auto-pass (returns `False`): `approved_pdf_exporter == True`

### `get_priority_level(data)` → `(level, hex_color, label)`
- `"high"` → `#8B0000` (dark red) — same criteria as above
- `"medium"` → `#FF8C00` (dark orange) — 5–20 violations/page
- `"low"` → `#006400` (dark green) — ≤4 violations/page or approved exporter

### `row_to_priority_data(row)` (`scripts/sharepoint_sync.py`)
Converts an Excel row dict (from Unique PDFs sheet) into a dict compatible with
`get_priority_level()`. Handles Excel type quirks; reconstructs `failed_checks`
from `Errors/Page × page_count` if needed.

---

## Reporting Scripts Relationships

### `historical_analysis.py`
- **Reads:** all timestamped `.xlsx` in each domain folder
- **Parses:** `Unique PDFs` sheet (falls back to `Scanned PDFs`)
- **Metrics extracted:** `unique_pdfs`, `compliance_pct` (Low Priority=Yes / total),
  `high_priority`, `errors_per_page_avg`, `violations_total`, `top_errors`
- **Outputs:** `{domain}/historical_analysis.html` — one per domain, overwritten each run
- **Core function:** `parse_excel_report(source)` → metrics dict; `collect_from_local(base_path, domains)` → `dict[domain: list[scan_dicts]]`

### `generate_master_report.py` (Excel)
- **Reads:** latest `.xlsx` per domain via `read_unique_pdfs_sheet()` and `count_pdfs()`
- **Writes:** `Master/Master Report.xlsx`
  - `Data` sheet: **accumulates** — appends one row per domain per run (historical log, never cleared)
  - `Dashboard` sheet: refreshed each run, shows latest totals + date dropdown
  - `Run Index` sheet: hidden, powers the dropdown
- **File locking:** retries 3× with 2s delay if Excel is open

### `generate_master_report_html.py` (HTML Dashboard)
- **Reads:** all `.xlsx` via `collect_from_local()` (imported from `historical_analysis.py`)
- **Writes:** `Master/master_report.html` — **fully overwritten** each run
- **Contains:** summary pills, trend insight banner, snapshot bar charts (compliance % and
  high-priority per domain, colour-coded), historical line charts (aggregate + per-domain),
  sortable domain table, per-domain cards with mini trend charts
- **Chart.js:** v4.4.0 from jsDelivr CDN; `_js()` uses HTML-safe JSON (escapes `<`, `>`, `&`)

**Run both together:**
```powershell
python scripts/generate_master_report.py ; python scripts/generate_master_report_html.py
```

---

## Configuration Values (config.py)

```python
INSTITUTION_NAME      = "Cal State LA"
INSTITUTION_DOMAIN    = "calstatela.edu"
ACCESSIBILITY_EMAIL   = "accessibility@calstatela.edu"
DATABASE_PATH         = PROJECT_ROOT / "drupal_pdfs.db"
PDF_SITES_FOLDER      = OUTPUT_DIR / "scans"        # spider output root
TEAMS_ONEDRIVE_PATH   = "~/OneDrive - Cal State LA/PDF Accessibility Checker (PAC) - General"
TEAMS_SHAREPOINT_FILES_URL = "https://csula.sharepoint.com/:x:/r/sites/PDFAccessibilityCheckerPAC/Shared%20Documents/General"
VERAPDF_COMMAND       = "~/veraPDF/verapdf.bat"     # auto-updated by setup.ps1
VERAPDF_PROFILE       = "ua1"
EXCEL_REPORT_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
OUTLOOK_SAVE_AS_MSG   = False     # True = save .msg instead of sending
OUTLOOK_DISPLAY_ONLY  = False     # True = open draft in Outlook, don't send
```

`DOMAINS` list is loaded from `data/sites.csv` (full URLs, one per line).

---

## Database Schema (SQLite)

```
drupal_pdf_files   — id, pdf_uri, parent_uri, scanned_date, drupal_site_id, file_hash, pdf_returns_404, parent_returns_404
pdf_report         — id, pdf_hash (UNIQUE), violations, failed_checks, tagged, pdf_text_type, title_set, language_set, page_count, has_form, approved_pdf_exporter
drupal_site        — id, domain_name, page_title, security_group_name, box_folder
site_user          — employee_id (PK), first_name, last_name, email, is_manager
site_assignment    — id, site_id (FK), user_id (FK) — links employees to domains
failure            — id, site_id, pdf_id, error_date, error_message
```

Deduplication: PDFs are identified by SHA-256 hash (`file_hash`). One `pdf_report`
row is shared by all occurrences of the same file hash. 404s are tracked per-URL.

---

## CSV Data Files

**`data/sites.csv`** — full URLs + security group, one per line:
```
https://www.calstatela.edu/admissions,CSULA-content-manager_pchauha5
```

**`data/employees.csv`** — employee directory:
```
Full Name,Employee ID,Email
Pavan Chauhan,pchauha5,pchauha5@calstatela.edu
```

**`data/site_assignments.csv`** — who manages which domain:
```
Security Group Name,Employee Name,Employee ID,Email
CSULA-content-manager_pchauha5,Pavan Chauhan,pchauha5,pchauha5@calstatela.edu
```

**`data/managers.csv`** — employee IDs of managers (one per line).

---

## Email Draft Generation

`sharepoint_sync.py` runs in two independent phases:
1. **Sync:** Copy local Excel → OneDrive domain folder (skips if no local file)
2. **Drafts:** For every domain folder in OneDrive, read the latest `.xlsx`, generate
   one `{employee_id}_draft.html` per assigned employee into `{domain}/Mail Drafts/`

`send_emails.py` reads those draft files and sends via Outlook COM. No DB needed.
Email subject: `"PDF Accessibility Report - Cal State LA"`. Attachment: latest `.xlsx`.

---

## Overwrite Behaviour Summary

| Output file | Behaviour |
|---|---|
| `{domain}-YYYY-MM-DD_HH-MM-SS.xlsx` | New file each scan (timestamped, old ones stay) |
| `{domain}/Mail Drafts/{employee_id}_draft.html` | Overwritten each sharepoint_sync run |
| `{domain}/historical_analysis.html` | Overwritten each historical_analysis run |
| `Master/master_report.html` | Overwritten each run |
| `Master/Master Report.xlsx` | File overwritten, but **Data sheet accumulates rows** |

---

## Common Commands

```powershell
# Full pipeline
.\scripts\run_workflow_smooth.ps1

# Sync Excel + generate email drafts
python scripts/sharepoint_sync.py

# Send emails (prompts confirmation)
python scripts/send_emails.py
python scripts/send_emails.py --force

# Both master reports
python scripts/generate_master_report.py ; python scripts/generate_master_report_html.py

# Per-domain trend dashboards
python scripts/historical_analysis.py
python scripts/historical_analysis.py --no-upload   # save locally instead of OneDrive
python scripts/historical_analysis.py --domains www.calstatela.edu_admissions

# Reset (backs up DB, clears outputs)
.\scripts\fresh_start.ps1
```

---

## Key Architectural Patterns

- **Single config file:** Everything routes through `config.py`. Never hardcode paths.
- **No DB for email step:** `sharepoint_sync.py` and `send_emails.py` read directly from OneDrive `.xlsx` files — no database access required.
- **HTML-safe JSON in scripts:** `_js()` in both `historical_analysis.py` and `generate_master_report_html.py` escapes `<`, `>`, `&` to prevent `</script>` in error-message data from breaking the `<script>` tag.
- **Chart.js guard:** Every `<script>` block that initialises charts starts with `if (typeof Chart === 'undefined') return;` to surface CDN failures clearly.
- **Restart-safe crawling:** `run_all_spiders.py` tracks completed spiders in a temp file; re-runs only unfinished spiders.
- **Unique PDF representative row:** `Unique PDFs` sheet picks the highest-severity row per PDF (most violations if any are high-priority).
- **Approved exporter shortcut:** If `approved_pdf_exporter = True`, the PDF is auto-classified as low priority regardless of other metrics.
- **CSULA brand colours:** Navy `#003262`, Gold `#C4820E`. Used consistently across all HTML dashboards.
