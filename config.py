"""
CSULA PDF Accessibility Checker - Central Configuration
========================================================

This file contains all configurable paths, settings, and parameters for the
CSULA PDF accessibility checking system. Update these values to match your
local environment and institution settings.

All other modules should import from this file instead of hardcoding paths.
"""

import os
from pathlib import Path

# =============================================================================
# PROJECT PATHS
# =============================================================================

# Base directory (where this config.py file is located)
BASE_DIR = Path(__file__).resolve().parent

# Project root directory
PROJECT_ROOT = BASE_DIR

# =============================================================================
# INSTITUTION SETTINGS
# =============================================================================

# Institution domain suffix (e.g., "calstatela.edu" for CSULA)
INSTITUTION_DOMAIN = "calstatela.edu"

# Institution name (for reports and communications)
INSTITUTION_NAME = "Cal State LA"

# Accessibility office email (for sending reports from)
ACCESSIBILITY_EMAIL = "accessibility@calstatela.edu"

# Test email recipient (for development/testing)
TEST_EMAIL_RECIPIENT = "pchauha5@calstatela.edu"

# Box.com domain pattern (if using Box for file storage)
BOX_DOMAIN_PATTERN = r'https://[a-zA-Z0-9.-]*\.box\.com/s/[a-zA-Z0-9]+'

# =============================================================================
# DIRECTORY PATHS
# =============================================================================

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
EMPLOYEES_CSV = DATA_DIR / "employees.csv"
EMPLOYEES1_CSV = DATA_DIR / "employees1.csv"
MANAGERS_CSV = DATA_DIR / "managers.csv"
SITE_ASSIGNMENTS_CSV = DATA_DIR / "site_assignments.csv"
SITES_CSV = DATA_DIR / "sites.csv"

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_REPORTS_DIR = OUTPUT_DIR / "reports"
OUTPUT_EMAILS_DIR = OUTPUT_DIR / "emails"
OUTPUT_BACKUPS_DIR = OUTPUT_DIR / "backups"

# Ensure output directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_REPORTS_DIR.mkdir(exist_ok=True)
OUTPUT_EMAILS_DIR.mkdir(exist_ok=True)
OUTPUT_BACKUPS_DIR.mkdir(exist_ok=True)

# Temporary files directory
TEMP_DIR = PROJECT_ROOT / "temp"
TEMP_DIR.mkdir(exist_ok=True)
TEMP_PDF_PATH = TEMP_DIR / "temp.pdf"
TEMP_PROFILE_PATH = TEMP_DIR / "temp_profile.json"

# SQL queries directory
SQL_DIR = PROJECT_ROOT / "sql"

# Documentation directory
DOCS_DIR = PROJECT_ROOT / "docs"

# Crawler/Spider directory
CRAWLERS_DIR = PROJECT_ROOT / "crawlers"
SPIDER_DIR = CRAWLERS_DIR / "sf_state_pdf_scan"

# =============================================================================
# DATABASE SETTINGS
# =============================================================================

# SQLite database path
DATABASE_PATH = PROJECT_ROOT / "drupal_pdfs.db"

# Database backup directory (optional - for storing database backups)
DB_BACKUP_DIR = OUTPUT_BACKUPS_DIR / "database"
DB_BACKUP_DIR.mkdir(exist_ok=True)

# =============================================================================
# PDF SCANNING SETTINGS
# =============================================================================

# Root folder where scanned PDFs and results are stored
# This is where spider output folders will be created (one per domain)
PDF_SITES_FOLDER = OUTPUT_DIR / "scans"
PDF_SITES_FOLDER.mkdir(exist_ok=True)

# Output format string for individual site scan results
# Usage: SCANS_OUTPUT_FORMAT.format("example-calstatela-edu")
SCANS_OUTPUT_FORMAT = str(PDF_SITES_FOLDER / "{}")

# =============================================================================
# VERAPDF SETTINGS
# =============================================================================

# VeraPDF command (should be in PATH, or provide full path here)
VERAPDF_COMMAND = r"C:\Users\pchauha4\veraPDF\verapdf.bat"

# VeraPDF validation profile (ua1, ua2, etc.)
VERAPDF_PROFILE = "ua1"


# VeraPDF output format
VERAPDF_FORMAT = "json"

# =============================================================================
# WEB CRAWLING SETTINGS
# =============================================================================

# Scrapy settings
CONCURRENT_REQUESTS = 16
DOWNLOAD_DELAY = 0.05
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Autothrottle settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Obey robots.txt
ROBOTSTXT_OBEY = False  # Set to True if you want to respect robots.txt

# =============================================================================
# EMAIL SETTINGS
# =============================================================================

# Email sender name and address
EMAIL_SENDER_NAME = "Cal State LA Accessibility Team"
# Used for display/metadata in templates and docs. Actual sending is done via Outlook COM.
EMAIL_SENDER_EMAIL = ACCESSIBILITY_EMAIL

# Default email subject line
EMAIL_SUBJECT = "PDF Accessibility Report - Cal State LA"

# Email template path
EMAIL_TEMPLATE_PATH = OUTPUT_DIR / "email_templates" / "email_template.html"


# Test Mode (dry run - doesn't actually send/save emails)
EMAIL_DRY_RUN = False

# =============================================================================
# OUTLOOK (WINDOWS) CONFIGURATION (for Outlook COM automation)
# =============================================================================

# If set, emails will be created "on behalf of" this address.
# This requires Exchange permissions. Leave as None to send as the signed-in mailbox.
OUTLOOK_SENT_ON_BEHALF_OF = ACCESSIBILITY_EMAIL

# Choose whether Outlook automation sends emails or saves draft .msg files.
# - False: send immediately via Outlook
# - True: save .msg files to OUTPUT_EMAILS_DIR/outlook_msg/
OUTLOOK_SAVE_AS_MSG = False
OUTLOOK_MSG_DIR = OUTPUT_EMAILS_DIR / "outlook_msg"
OUTLOOK_MSG_DIR.mkdir(exist_ok=True)

# If True, opens the draft window in Outlook instead of sending.
OUTLOOK_DISPLAY_ONLY = False

# =============================================================================
# EMAIL SENDING OPTIONS
# =============================================================================

# Enable/Disable automatic email sending
ENABLE_EMAIL_SENDING = True            # Set to False to disable email sending

# Save email copies to file (for records)
SAVE_EMAIL_COPIES = True               # Save sent emails as .eml files for records
EMAIL_COPIES_DIR = OUTPUT_EMAILS_DIR / "sent"
EMAIL_COPIES_DIR.mkdir(exist_ok=True)

# =============================================================================
# REPORTING SETTINGS
# =============================================================================

# Monthly report HTML template
MONTHLY_REPORT_TEMPLATE = OUTPUT_REPORTS_DIR / "monthly_report.html"

# Excel report settings
# Excel report settings
# New default report naming: {domain_name}-{YYYY-MM-DD_HH-MM-SS}.xlsx
# Example: www.calstatela.edu_accessibility-2026-01-25_06-26-57.xlsx
EXCEL_REPORT_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
EXCEL_REPORT_NAME_FORMAT = "{domain_name}-{timestamp}.xlsx"

# =============================================================================
# SCAN DOMAIN LIST
# =============================================================================

# Domains are loaded from data/sites.csv (first column, no header).
# The CSV uses full URLs (e.g. https://www.calstatela.edu/admissions).
# They are converted to the internal key format (e.g. www.calstatela.edu_admissions)
# by stripping the scheme and replacing path slashes with underscores.
import csv as _csv

def _url_to_domain_key(raw: str) -> str:
    """Convert a full URL or bare domain to the internal domain key format.
    https://www.calstatela.edu/admissions  ->  www.calstatela.edu_admissions
    https://discover.calstatela.edu        ->  discover.calstatela.edu
    www.calstatela.edu_admissions          ->  www.calstatela.edu_admissions  (pass-through)
    """
    s = raw.strip()
    # Strip scheme
    if "://" in s:
        s = s.split("://", 1)[1]
    # Strip trailing slashes
    s = s.rstrip("/")
    # Replace path slashes with underscores
    s = s.replace("/", "_")
    return s

def _load_domains_from_csv(csv_path):
    domains = []
    if csv_path.exists():
        with open(csv_path, newline="", encoding="utf-8") as _f:
            for row in _csv.reader(_f):
                if row and row[0].strip():
                    domains.append(_url_to_domain_key(row[0]))
    return domains

DOMAINS = _load_domains_from_csv(SITES_CSV)

# Backwards-compatible aliases (older code may still import these).
TEST_DOMAINS = DOMAINS
USE_TEST_DOMAINS_ONLY = True

# =============================================================================
# MICROSOFT TEAMS / ONEDRIVE SETTINGS
# =============================================================================
# Both scripts/teams_upload.py and scripts/historical_analysis.py use the
# OneDrive-synced Teams folder directly — no API or authentication required.
#
# How to find TEAMS_ONEDRIVE_PATH:
#   Your Teams channel Files tab is synced to your local machine via OneDrive.
#   Open File Explorer → look under "OneDrive - Cal State LA" for the folder
#   named after your team (e.g. "PDF Accessibility Checker (PAC) - General").

# Root folder synced from your Teams channel Files tab
TEAMS_ONEDRIVE_PATH = r"C:\Users\pchauha4\OneDrive - Cal State LA\PDF Accessibility Checker (PAC) - General"

# SharePoint base URL for direct Excel file links in historical_analysis.py dashboards.
# Format: https://<tenant>.sharepoint.com/:x:/r/sites/<SiteName>/Shared%20Documents/<FolderPath>
# Leave blank to disable hyperlinks on timestamps.
TEAMS_SHAREPOINT_FILES_URL = "https://csula.sharepoint.com/:x:/r/sites/PDFAccessibilityCheckerPAC/Shared%20Documents/General"

# =============================================================================
# LOGGING SETTINGS
# =============================================================================

# Log directory
LOG_DIR = OUTPUT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log file path
LOG_FILE = LOG_DIR / "pdf_checker.log"

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_domain_folder_name(domain_name):
    """
    Convert domain name to folder-safe format.
    Example: "www.calstatela.edu" -> "www-calstatela-edu"
    """
    name = normalize_domain_key(domain_name)
    return name.replace(".", "-")


def normalize_domain_key(domain_name: str) -> str:
    """Normalize a domain key for consistent folder/report naming."""
    if domain_name is None:
        return ""

    name = str(domain_name).strip()
    if "://" in name:
        name = name.split("://", 1)[1]
    name = name.strip("/")
    if name.lower().startswith("www."):
        name = name[4:]
    return name


def get_site_output_path(domain_name):
    """
    Get the output path for a specific domain's scan results.
    
    Args:
        domain_name (str): Domain name (e.g., "www.calstatela.edu")
    
    Returns:
        Path: Path object for the domain's output directory
    """
    normalized = normalize_domain_key(domain_name)

    # Prefer an existing directory if one already exists under either naming.
    candidates = []
    if normalized:
        candidates.append(PDF_SITES_FOLDER / get_domain_folder_name(normalized))

    # Legacy naming: sometimes includes leading "www.".
    if normalized and not normalized.lower().startswith("www."):
        legacy_with_www = f"www.{normalized}"
        candidates.append(PDF_SITES_FOLDER / legacy_with_www.replace(".", "-"))

    for path in candidates:
        if path.exists() and path.is_dir():
            return path

    # Default to normalized folder naming.
    if not normalized:
        normalized = str(domain_name).strip()
    return PDF_SITES_FOLDER / get_domain_folder_name(normalized)


def get_excel_report_path(domain_name, *, timestamp=None, prefer_latest=True):
    """
    Get the Excel report path for a specific domain.

    By default this returns the most recently generated report in the domain's
    output folder (supports both the new timestamped naming and legacy names).
    Set prefer_latest=False to get a new timestamped path for generating a
    fresh report.
    
    Args:
        domain_name (str): Domain name (e.g., "www.calstatela.edu")
    
    Returns:
        Path: Path object for the Excel report file
    """
    site_path = get_site_output_path(domain_name)
    site_path.mkdir(parents=True, exist_ok=True)

    # Consumers (emails, tooling) usually want the newest report.
    if prefer_latest:
        # New naming convention.
        candidates = list(site_path.glob(f"{domain_name}-*.xlsx"))
        # Legacy naming convention(s).
        candidates.extend(site_path.glob("*-pdf-scans*.xlsx"))
        # Ignore Excel temp/lock files.
        candidates = [p for p in candidates if p.is_file() and not p.name.startswith("~$")]
        if candidates:
            return max(candidates, key=lambda p: p.stat().st_mtime)

    if timestamp is None:
        from datetime import datetime

        timestamp = datetime.now().strftime(EXCEL_REPORT_TIMESTAMP_FORMAT)

    report_name = EXCEL_REPORT_NAME_FORMAT.format(domain_name=domain_name, timestamp=timestamp)
    return site_path / report_name


def get_backup_path(filename, timestamp=True):
    """
    Get a backup file path with optional timestamp.
    
    Args:
        filename (str): Original filename
        timestamp (bool): Whether to add timestamp to filename
    
    Returns:
        Path: Path object for the backup file
    """
    if timestamp:
        from datetime import datetime
        ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2:
            filename = f"{name_parts[0]}-{ts}.{name_parts[1]}"
        else:
            filename = f"{filename}-{ts}"
    
    return OUTPUT_BACKUPS_DIR / filename


# =============================================================================
# VALIDATION
# =============================================================================

def validate_config():
    """
    Validate that all required paths and settings are properly configured.
    Raises an exception if configuration is invalid.
    """
    errors = []
    
    # Check required directories exist
    if not DATA_DIR.exists():
        errors.append(f"Data directory does not exist: {DATA_DIR}")
    
    if not SQL_DIR.exists():
        errors.append(f"SQL directory does not exist: {SQL_DIR}")
    
    # Check required CSV files exist
    if not SITES_CSV.exists():
        errors.append(f"Sites CSV file does not exist: {SITES_CSV}")
    
    # Validate institution settings
    if not INSTITUTION_DOMAIN:
        errors.append("INSTITUTION_DOMAIN must be set")
    
    if not INSTITUTION_NAME:
        errors.append("INSTITUTION_NAME must be set")
    
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)
    
    return True


# =============================================================================
# DISPLAY CONFIGURATION (for debugging)
# =============================================================================

def print_config():
    """Print current configuration settings."""
    print("=" * 70)
    print("CSULA PDF Checker Configuration")
    print("=" * 70)
    print(f"Institution: {INSTITUTION_NAME}")
    print(f"Domain: {INSTITUTION_DOMAIN}")
    print(f"Database: {DATABASE_PATH}")
    print(f"PDF Sites Folder: {PDF_SITES_FOLDER}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"Temp Directory: {TEMP_DIR}")
    print(f"Domains: {', '.join(DOMAINS)}")
    print("=" * 70)


# Auto-validate on import (optional - comment out if you want manual validation)
if __name__ != "__main__":
    try:
        validate_config()
    except ValueError as e:
        print(f"Warning: {e}")
        print("Please update config.py with correct settings.")


# =============================================================================
# MAIN - For testing configuration
# =============================================================================

if __name__ == "__main__":
    print_config()
    try:
        validate_config()
        print("\n✅ Configuration is valid!")
    except ValueError as e:
        print(f"\n❌ Configuration validation failed:\n{e}")
