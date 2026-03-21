# Project Structure Overview

## New Organized Structure (CSULA-homegrownPAC/)

```
CSULA-homegrownPAC/
│
├── 📄 master_functions.py         # MAIN ORCHESTRATOR - Start here!
├── 📄 README.md                   # Project documentation
├── 📄 .gitignore                  # Git ignore rules
│
├── 📁 config/                     # Configuration & Settings
│   ├── priority_profiles.py      # Priority detection profiles
│   ├── sites.py                  # Site configurations
│   └── README.md
│
├── 📁 src/                        # Source Code (organized by function)
│   ├── __init__.py
│   │
│   ├── 📁 core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── database.py           # Database schema
│   │   ├── conformance_checker.py # VeraPDF testing
│   │   ├── pdf_priority.py       # PDF analysis algorithms
│   │   ├── filters.py            # Priority & filtering
│   │   └── scan_refresh.py       # 404 checking
│   │
│   ├── 📁 data_management/        # Data layer
│   │   ├── __init__.py
│   │   ├── data_import.py        # CSV → Database
│   │   ├── data_export.py        # Database → Excel
│   │   └── doa_import.py         # DOA imports
│   │
│   ├── 📁 reporting/              # Report generation
│   │   ├── __init__.py
│   │   └── html_report.py        # HTML dashboard
│   │
│   ├── 📁 communication/          # Email automation
│   │   ├── __init__.py
│   │   ├── communications.py     # Email content
│   │   ├── pdf_email.py          # Email sending
│   │   └── admin_email.py        # Admin notifications
│   │
│   └── 📁 utilities/              # Helper functions
│       ├── __init__.py
│       └── tools.py              # Utility tools
│
├── 📁 scripts/                    # Automation scripts
│   ├── send_emails.py            # Email sending (Outlook - Windows)
│   ├── teams_upload.py           # Copy Excel reports to Teams via OneDrive sync
│   └── historical_analysis.py   # Per-domain HTML trend dashboards from timestamped reports
│
├── 📁 crawlers/                   # Web scraping
│   ├── README.md
│   └── 📁 csula_pdf_scan/     # Scrapy project
│       ├── run_all_spiders.py    # Spider orchestrator
│       ├── run_spider_by_name.py
│       ├── scrapy.cfg
│       └── csula_pdf_scan/
│           ├── __init__.py
│           ├── box_handler.py    # Box.com integration
│           ├── items.py
│           ├── middlewares.py
│           ├── pipelines.py
│           ├── settings.py
│           └── spiders/
│               ├── __init__.py
│               └── faculty_spider.py
│
├── 📁 sql/                        # SQL query library
│   ├── README.md
│   ├── get_all_sites.sql
│   ├── get_pdf_reports_by_site_name.sql
│   ├── get_pdfs_by_domain_name.sql
│   ├── get_all_pdfs.sql
│   ├── get_failures_by_site_id.sql
│   ├── delete_duplicates.sql
│   └── ... (14 total SQL files)
│
├── 📁 data/                       # CSV input data
│   ├── README.md
│   ├── employees.csv
│   ├── employees1.csv
│   ├── managers.csv
│   ├── sites.csv
│   └── site_assignments.csv
│
├── 📁 output/                     # All generated outputs
│   ├── README.md
│   ├── 📁 reports/               # Excel & HTML reports
│   │   └── monthly_report.html
│   ├── 📁 emails/                # Email MSG files
│   └── 📁 backups/               # Database backups
│
├── 📁 docs/                       # Documentation
│   ├── instructions.md
│   └── 📁 info/                  # ADA compliance docs
│       ├── ADA_Title_II_Accessible_Content_Responsibilities.txt
│       ├── D_Part_PDF_Decision_Checklist.txt
│       └── Drupal_PDF_Accessibility_Review.txt
│
├── 📁 temp/                       # Temporary processing files
│   └── README.md                 # (temp.pdf, temp_profile.json)
│
└── 🗄️ drupal_pdfs.db             # SQLite database (auto-created)
```

## Key Improvements

### 1. **Logical Grouping**
   - Core modules separated from data management
   - Reporting and communication isolated
   - Clear separation of concerns

### 2. **Output Organization**
   - All generated files go to `output/`
   - Subdirectories for different output types
   - Easy to backup or clean

### 3. **Clear Entry Points**
   - `master_functions.py` at root = main orchestrator
   - Each folder has README.md explaining its purpose
   - __init__.py files for proper Python packages

### 4. **Better Navigation**
   - Related files grouped together
   - No more scattered modules in root
   - Documentation in dedicated `docs/` folder

### 5. **Professional Structure**
   - Follows Python best practices
   - Easy to understand for new developers
   - Scalable for future additions

## Quick Navigation Guide

| Task | Location |
|------|----------|
| Run full workflow | `master_functions.py` |
| Configure priorities | `config/priority_profiles.py` |
| Manage database | `src/core/database.py` |
| Test PDFs | `src/core/conformance_checker.py` |
| Import data | `src/data_management/data_import.py` |
| Generate reports | `src/reporting/html_report.py` |
| Send emails | `src/communication/pdf_email.py` |
| Upload reports to Teams | `scripts/teams_upload.py` |
| Historical trend dashboards | `scripts/historical_analysis.py` |
| Web scraping | `crawlers/csula_pdf_scan/` |
| SQL queries | `sql/*.sql` |
| View outputs | `output/reports/` |
| Read docs | `docs/` |

## Migration Notes

All files have been copied from `csula_pdf_check-master/` to the new organized structure. No functionality has changed - only the organization.

**Note**: Update any hardcoded paths in the code to reflect the new structure if needed.
