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
VERAPDF_COMMAND = "verapdf"

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

# Email template path
EMAIL_TEMPLATE_PATH = OUTPUT_DIR / "email_templates" / "email_template.html"

# Email sending method ("outlook_com", "smtp", or "none")
EMAIL_METHOD = "none"  # Options: "outlook_com", "smtp", "none"

# SMTP settings (if EMAIL_METHOD is "smtp")
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USE_TLS = True
SMTP_USERNAME = ""  # Your email username
SMTP_PASSWORD = ""  # Your email password or app-specific password

# =============================================================================
# REPORTING SETTINGS
# =============================================================================

# Monthly report HTML template
MONTHLY_REPORT_TEMPLATE = OUTPUT_REPORTS_DIR / "monthly_report.html"

# Excel report settings
EXCEL_REPORT_NAME_FORMAT = "{site_name}-pdf-scans.xlsx"

# =============================================================================
# TEST/DEVELOPMENT SETTINGS
# =============================================================================

# Test domains (for initial testing with a subset of domains)
# Note: Use underscore (_) instead of slash (/) for URL paths
TEST_DOMAINS = [
    "www.calstatela.edu_accessibility",
]

# Use test domains only (set to False for production)
USE_TEST_DOMAINS_ONLY = True

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
    return domain_name.replace(".", "-")


def get_site_output_path(domain_name):
    """
    Get the output path for a specific domain's scan results.
    
    Args:
        domain_name (str): Domain name (e.g., "www.calstatela.edu")
    
    Returns:
        Path: Path object for the domain's output directory
    """
    folder_name = get_domain_folder_name(domain_name)
    return PDF_SITES_FOLDER / folder_name


def get_excel_report_path(domain_name):
    """
    Get the Excel report path for a specific domain.
    
    Args:
        domain_name (str): Domain name (e.g., "www.calstatela.edu")
    
    Returns:
        Path: Path object for the Excel report file
    """
    folder_name = get_domain_folder_name(domain_name)
    site_path = get_site_output_path(domain_name)
    report_name = EXCEL_REPORT_NAME_FORMAT.format(site_name=folder_name.split('-')[0])
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
    print(f"Test Mode: {USE_TEST_DOMAINS_ONLY}")
    if USE_TEST_DOMAINS_ONLY:
        print(f"Test Domains: {', '.join(TEST_DOMAINS)}")
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
