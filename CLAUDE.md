# CLAUDE.md — CSULA HomegrownPAC

## Instructions for Claude

- **Never add `Co-Authored-By:` lines to git commits.** The user does not want any Claude attribution in the repository history. Commit with the user's name only, always.

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
                →  data_export.py → {domain}-YYYY-MM-DD_HH-MM-SS.xlsx
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
| `src/core/filters.py` | `is_high_priority()`, `get_priority_level()` — priority thresholds |
| `src/data_management/report_reader.py` | **Central shared library** — all Excel reading, parsing, dedup, row utilities, path helpers, HTML-safe JSON. Every reporting script imports from here. |
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

## Centralised Logic Architecture — CRITICAL

**`src/data_management/report_reader.py` is the single source of truth for all shared logic.**
No reporting script owns a private copy of any function used by another script.
This was the root cause of count mismatches between reports — now eliminated.

### What lives in `report_reader.py`

| Function | Purpose |
|---|---|
| `parse_domain_excel(source)` | Canonical aggregate parser — fingerprint-dedup, reads `Low Priority` column, returns metrics dict |
| `collect_from_local(base_path, domains)` | Reads all timestamped Excel files across domain folders |
| `read_pdf_rows(xlsx_path)` | Raw row reader for per-PDF email content (no dedup) |
| `row_to_priority_data(row)` | Converts Excel row to dict for display metrics |
| `find_latest_xlsx(folder)` | Returns most recent timestamped `.xlsx` in a folder |
| `folder_to_display_name(folder_name)` | OneDrive folder name → readable domain string |
| `xlsx_report_date(xlsx_path)` | Extracts human-readable date from Excel filename |
| `_parse_timestamp(filename)` | Extracts datetime from Excel filename |
| `_TIMESTAMP_RE` | Shared timestamp regex |
| `_strip_hyperlink(val)` | Extracts bare URL from Excel `=HYPERLINK()` formula |
| `_coerce_int(val)`, `_coerce_bool(val)` | Excel cell type coercion |
| `_js(obj)` | HTML-safe JSON serializer for `<script>` blocks |

### What lives in `src/core/filters.py`

| Function | Purpose |
|---|---|
| `is_high_priority(data)` | Called by `data_export.py` at scan time to stamp `Low Priority` column |
| `get_priority_level(data)` | Returns `(level, color, label)` — used only for per-PDF display metrics |

### Priority source of truth
The `Low Priority` column in each Excel file is stamped by `data_export.py` using
`is_high_priority()` at scan time. All reporting scripts read that stamped column value —
**never re-evaluating filter logic from raw row data** — so every report shows identical counts.

---

## Priority Thresholds (calibrated against 5,573 CSULA PDFs)

### `is_high_priority(data)` → bool
Returns `True` if ANY of:
- `tagged == 0` — untagged, screen readers cannot navigate
- `pdf_text_type == "Image Only"` — no text layer, completely inaccessible
- `errors/page > 9` — systematic accessibility failures across most content
- `has_form == 1` AND `errors/page > 3` — forms must be fully accessible under ADA

Auto-pass: `approved_pdf_exporter == True` → always low priority regardless of counts.

### `get_priority_level(data)` → `(level, hex_color, label)`
- `"high"` → `#8B0000` — same criteria as `is_high_priority()`
- `"medium"` → `#FF8C00` — tagged, `4–9 errors/page` (real WCAG violations, still navigable)
- `"low"` → `#006400` — tagged, `0–3 errors/page`, or approved exporter

### Why these thresholds
Data distribution from diagnostic scan:
- 0 PDFs had >20 errors/page (old threshold was dead code)
- 1,560 PDFs (28%) are untagged — the real high-priority driver
- 1,809 PDFs (32.5%) have 4–9 errors/page — medium priority
- Only 31 PDFs (0.6%) have 10–19 errors/page — high priority by errors threshold

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
├── calstatela-edu-admissions/
│   ├── calstatela.edu_admissions-2026-01-25_06-26-57.xlsx   ← timestamped reports accumulate
│   ├── historical_analysis.html          ← overwritten each run
│   └── Mail Drafts/
│       ├── pchauha5_draft.html           ← overwritten each run
│       └── jsmith_draft.html
├── calstatela-edu-ecst/
│   └── ...
└── Master/                              ← always write here, never in root
    ├── Master Report.xlsx               ← Data sheet accumulates; Dashboard refreshed
    └── master_report.html               ← fully overwritten each run
```

The `Master/` subfolder is created automatically. Both master report scripts must
always write there — never to the OneDrive root directly.

---

## Excel Report Structure (per-domain)

**Sheet: Unique PDFs** — deduplicated by `fingerprint` (SHA-256); one row per actual PDF file.
This is the primary sheet read by all reporting/master scripts via `parse_domain_excel()`.

**Sheet: Scanned PDFs** — one row per PDF occurrence (same file on multiple pages = multiple rows).

**Key columns:**

| Column | Description |
|---|---|
| `pdf_uri` | Hyperlinked PDF URL (=HYPERLINK formula) |
| `parent_uri` | Hyperlinked page containing the PDF |
| `violations` | VeraPDF PDF/UA 1.0 violation count |
| `failed_checks` | Count of failed accessibility checks |
| `tagged` | 1/0 — structurally tagged |
| `pdf_text_type` | "Text Only" / "Image Only" / "Image Over Text" / "No Image or Text" |
| `page_count` | Total pages |
| `has_form` | 1/0 — contains form fields |
| `approved_pdf_exporter` | 1/0 — created by approved tool (e.g. Equidox 7) |
| `Errors/Page` | Computed: `violations / page_count` |
| `Low Priority` | Stamped by `data_export.py`: "No" = high priority, "Yes" = compliant |
| `fingerprint` | SHA-256 hash — dedup key in `parse_domain_excel()` |

**High-priority rows** get red fill. **Other sheets:** Grouped by PDF URL, Grouped by Parent URL, Failure, Instructions.

---

## Reporting Scripts — How They Work

### `historical_analysis.py`
- Imports `parse_domain_excel`, `collect_from_local`, `_js` from `report_reader`
- Reads all timestamped `.xlsx` per domain folder (full scan history)
- Outputs: `{domain}/historical_analysis.html` — overwritten each run

### `generate_master_report.py` (Excel)
- Imports `parse_domain_excel`, `find_latest_xlsx`, `folder_to_display_name` from `report_reader`
- Reads latest `.xlsx` per domain (not full history)
- Writes `Master/Master Report.xlsx`:
  - `Data` sheet: accumulates — **deduplicates by (scan_date, domain) so re-runs don't add duplicate rows**
  - `Dashboard` sheet: refreshed each run with latest totals + date dropdown
  - `Run Index` sheet: hidden, powers dropdown

### `generate_master_report_html.py` (HTML Dashboard)
- Imports `collect_from_local`, `_js` from `report_reader`
- Reads all `.xlsx` history (same as historical_analysis)
- Writes `Master/master_report.html` — fully overwritten each run

### `sharepoint_sync.py`
- Imports `find_latest_xlsx`, `folder_to_display_name`, `xlsx_report_date`, `read_pdf_rows`, `row_to_priority_data`, `_strip_hyperlink` from `report_reader`
- Priority in email drafts comes from `Low Priority` column (same source as reports)
- Deduplicates by fingerprint before building email PDF list

---

## Common Commands

```powershell
# Full workflow — crawl + scan + export Excel + sync + all reports
.\scripts\run_workflow_smooth.ps1 ; python scripts/sharepoint_sync.py ; python scripts/historical_analysis.py ; python scripts/generate_master_report.py ; python scripts/generate_master_report_html.py

# Regenerate reports from existing DB (no re-crawl needed)
python scripts/data_export.py ; python scripts/sharepoint_sync.py ; python scripts/historical_analysis.py ; python scripts/generate_master_report.py ; python scripts/generate_master_report_html.py

# Send emails (prompts confirmation)
python scripts/send_emails.py
python scripts/send_emails.py --force

# Per-domain trend dashboards only
python scripts/historical_analysis.py
python scripts/historical_analysis.py --no-upload
python scripts/historical_analysis.py --domains www.calstatela.edu_admissions

# Reset (backs up DB, clears outputs)
.\scripts\fresh_start.ps1
```

---

## Configuration Values (config.py)

```python
INSTITUTION_NAME      = "Cal State LA"
INSTITUTION_DOMAIN    = "calstatela.edu"
ACCESSIBILITY_EMAIL   = "accessibility@calstatela.edu"
DATABASE_PATH         = PROJECT_ROOT / "drupal_pdfs.db"
PDF_SITES_FOLDER      = OUTPUT_DIR / "scans"
TEAMS_ONEDRIVE_PATH   = "~/OneDrive - Cal State LA/PDF Accessibility Checker (PAC) - General"
VERAPDF_COMMAND       = "~/veraPDF/verapdf.bat"
VERAPDF_PROFILE       = "ua1"
EXCEL_REPORT_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
OUTLOOK_SAVE_AS_MSG   = False
OUTLOOK_DISPLAY_ONLY  = False
```

`DOMAINS` list loaded from `data/sites.csv` (full URLs, one per line).

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

Deduplication: PDFs identified by SHA-256 hash. One `pdf_report` row shared by all
occurrences of the same file. 404s tracked per-URL in `drupal_pdf_files`.

---

## CSV Data Files

**`data/sites.csv`** — full URLs + security group:
```
https://www.calstatela.edu/admissions,CSULA-content-manager_pchauha5
```

**`data/employees.csv`** — employee directory (with header row):
```
Full Name,Employee ID,Email
```

**`data/site_assignments.csv`** — who manages which domain:
```
Security Group Name,Employee Name,Employee ID,Email
```

**`data/managers.csv`** — employee IDs of managers (one per line).

---

## Email Draft Generation

`sharepoint_sync.py` runs in two independent phases:
1. **Sync:** Copy local Excel → OneDrive domain folder
2. **Drafts:** Read latest `.xlsx` from OneDrive folder, generate one `{employee_id}_draft.html`
   per assigned employee into `{domain}/Mail Drafts/`

Priority in email drafts matches reports exactly — both read `Low Priority` column via
`report_reader`. Email shows High (needs remediation) and Low (compliant) — no medium category.

`send_emails.py` reads draft files and sends via Outlook COM. No DB access needed.

---

## Overwrite Behaviour Summary

| Output file | Behaviour |
|---|---|
| `{domain}-YYYY-MM-DD_HH-MM-SS.xlsx` | New file each scan (old ones stay) |
| `{domain}/Mail Drafts/{employee_id}_draft.html` | Overwritten each sharepoint_sync run |
| `{domain}/historical_analysis.html` | Overwritten each historical_analysis run |
| `Master/master_report.html` | Overwritten each run |
| `Master/Master Report.xlsx` | Data sheet accumulates; **deduplicates by (scan_date, domain)** |

---

## Engineering Standards — Production-Grade Mindset

This is a university-wide compliance system. Every change must be made with the same rigour as production software. The root cause of the March 2026 count-mismatch incident was scripts each maintaining private copies of shared logic — this class of problem must never recur.

### Rules to follow on every change

**No duplicated logic.**
If two scripts need the same function, that function lives in one place and both import it.
Never copy-paste a function into a second script — create or extend the shared module.
Shared modules: `report_reader.py` (Excel/data), `filters.py` (priority), `config.py` (paths/settings).

**One source of truth per value.**
Every number that appears in multiple reports (unique PDFs, high priority count, compliance %)
must trace back to a single code path. If the same value is computed two different ways,
it will eventually diverge. Trace the source before adding any new metric to any report.

**No re-evaluation of already-stamped data.**
`Low Priority` is stamped by `data_export.py` at scan time using `is_high_priority()`.
Downstream scripts read that column — they never re-evaluate priority from raw row data.
If a threshold changes, update `filters.py` and re-run `data_export.py`. Do not add
threshold logic anywhere else.

**Deduplication must be consistent.**
All aggregate counts use fingerprint-deduped rows via `parse_domain_excel()`.
Per-PDF detail views (emails) use `read_pdf_rows()` but still dedup by fingerprint
before counting totals. Never count raw rows for a metric that claims to count unique PDFs.

**Check for existing shared utilities before writing a new one.**
Before writing `_coerce_int`, `_parse_timestamp`, `find_latest_xlsx`, etc. — check
`report_reader.py` first. The function likely already exists.

**Idempotent writes.**
Scripts that accumulate data (e.g. Master Report.xlsx Data sheet) must deduplicate
before appending. Running a script twice must produce the same result as running it once.
Check for existing (scan_date, domain) or equivalent key before inserting.

**Test cross-script consistency after any logic change.**
After any change to `filters.py`, `report_reader.py`, or `data_export.py`, regenerate
all reports and verify the same domain shows identical numbers in:
historical_analysis.html, master_report.html, Master Report.xlsx, and email drafts.

---

## Key Architectural Patterns

- **Single config file:** Everything routes through `config.py`. Never hardcode paths.
- **Centralised reader:** All Excel parsing, counting, dedup, and utilities live in `report_reader.py`. No script owns private copies of shared logic.
- **Priority stamped at export time:** `data_export.py` calls `is_high_priority()` and writes `Low Priority = No/Yes` into Excel. All downstream scripts read that column — never re-evaluate from row data.
- **Fingerprint deduplication:** `parse_domain_excel()` deduplicates by SHA-256 `fingerprint` column. High-priority flag wins if the same PDF appears twice.
- **No DB for reporting:** All reporting scripts read from OneDrive `.xlsx` files only. DB is only touched by `conformance_checker.py` (write) and `data_export.py` (read).
- **HTML-safe JSON:** `_js()` in `report_reader.py` escapes `<`, `>`, `&` — prevents `</script>` in VeraPDF error messages from breaking HTML script tags.
- **Chart.js guard:** Every chart `<script>` starts with `if (typeof Chart === 'undefined') return;` to surface CDN failures clearly.
- **Restart-safe crawling:** `run_all_spiders.py` tracks completed spiders in a temp file.
- **CSULA brand colours:** Navy `#003262`, Gold `#C4820E` — used across all HTML dashboards.
