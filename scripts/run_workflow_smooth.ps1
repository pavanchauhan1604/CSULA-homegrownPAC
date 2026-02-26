# =============================================================================
# CSULA PDF Accessibility Checker - Complete Workflow (PowerShell)
# Equivalent of scripts/run_workflow_smooth.sh
# =============================================================================
# Usage (from project root):
#   .\scripts\run_workflow_smooth.ps1
# =============================================================================

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$PYTHON = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
Write-Host "Using Python: $PYTHON"
Write-Host ""

# ---------------------------------------------------------------------------
# Step 0: Setup Database
# ---------------------------------------------------------------------------
Write-Host "============================================================"
Write-Host "STEP 0: Setup/Verify Database (Non-Destructive)"
Write-Host "============================================================"
Write-Host "(This will NOT delete drupal_pdfs.db; use fresh_start.ps1 for a clean reset.)"
Write-Host ""
& $PYTHON scripts\setup_test_environment.py --force --no-reset
Write-Host "Step 0 complete."
Write-Host ""

# ---------------------------------------------------------------------------
# Step 1: Generate Spiders
# ---------------------------------------------------------------------------
Write-Host "============================================================"
Write-Host "STEP 1: Generate Spiders for Domains"
Write-Host "============================================================"
& $PYTHON config\generate_spiders.py
Write-Host "Step 1 complete."
Write-Host ""

# ---------------------------------------------------------------------------
# Step 2: Run Spiders
# ---------------------------------------------------------------------------
Write-Host "============================================================"
Write-Host "STEP 2: Crawl Websites to Find PDFs"
Write-Host "============================================================"
Write-Host "This will take 5-15 minutes..."
Write-Host ""
Push-Location crawlers\sf_state_pdf_scan
try {
    & ..\..\$PYTHON run_all_spiders.py
} finally {
    Pop-Location
}
Write-Host "Step 2 complete."
Write-Host ""

# ---------------------------------------------------------------------------
# Step 3: Check Crawl Results
# ---------------------------------------------------------------------------
Write-Host "============================================================"
Write-Host "STEP 3: Check Crawl Results"
Write-Host "============================================================"
Get-ChildItem -Path output\scans -Recurse -Filter scanned_pdfs.txt |
    ForEach-Object { $c = (Get-Content $_.FullName | Measure-Object -Line).Lines; Write-Host "$c $($_.FullName)" }
Write-Host "Step 3 complete."
Write-Host ""

# ---------------------------------------------------------------------------
# Step 4: Analyze PDFs
# ---------------------------------------------------------------------------
Write-Host "============================================================"
Write-Host "STEP 4: Analyze PDFs for Accessibility"
Write-Host "============================================================"
Write-Host "This will take 30-60 minutes depending on number of PDFs..."
Write-Host ""
& $PYTHON -c @"
import sys
sys.path.insert(0, 'src/core')
sys.path.insert(0, 'src/data_management')
sys.path.insert(0, 'src/utilities')
print('Importing modules...')
from master_functions import create_all_pdf_reports
print('Starting PDF analysis...')
create_all_pdf_reports()
print('PDF analysis complete!')
"@
Write-Host "Step 4 complete."
Write-Host ""

# ---------------------------------------------------------------------------
# Step 5: Generate Excel Reports
# ---------------------------------------------------------------------------
Write-Host "============================================================"
Write-Host "STEP 5: Generate Excel Reports"
Write-Host "============================================================"
& $PYTHON -c @"
import sys
sys.path.insert(0, 'src/data_management')
sys.path.insert(0, 'src/core')
sys.path.insert(0, 'src/reporting')
print('Importing modules...')
from master_functions import build_all_xcel_reports
print('Generating Excel reports...')
build_all_xcel_reports()
print('Excel reports complete!')
"@
Write-Host "Step 5 complete."
Write-Host ""

# ---------------------------------------------------------------------------
# Step 6: Generate Email Reports
# ---------------------------------------------------------------------------
Write-Host "============================================================"
Write-Host "STEP 6: Generate Email Reports"
Write-Host "============================================================"
& $PYTHON -c @"
import sys, os
sys.path.insert(0, 'src/communication')
print('Importing modules...')
from communications import build_emails
print('Generating email reports...')
emails = build_emails()
os.makedirs('output/emails', exist_ok=True)
for idx, item in enumerate(emails, 1):
    email_html, recipient, attachments = item[0], item[1], item[2]
    filename = f'output/emails/email_{idx}_{recipient.replace(chr(64), "_at_").replace(".", "_")}.html'
    with open(filename, 'w') as f:
        f.write(email_html)
    print(f'  Saved: {filename}')
print('Email reports complete!')
"@
Write-Host "Step 6 complete."
Write-Host ""

# ---------------------------------------------------------------------------
# Step 7: Results Summary
# ---------------------------------------------------------------------------
Write-Host "============================================================"
Write-Host "STEP 7: Results Summary"
Write-Host "============================================================"
& $PYTHON -c @"
import sqlite3
conn = sqlite3.connect('drupal_pdfs.db')
c = conn.cursor()
print('Results Summary')
print('='*60)
c.execute('SELECT COUNT(*) FROM drupal_pdf_files')
print(f'Total PDFs found: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM pdf_report')
print(f'PDFs analyzed: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM pdf_report WHERE violations > 0')
print(f'PDFs with violations: {c.fetchone()[0]}')
c.execute('SELECT AVG(violations) FROM pdf_report WHERE violations > 0')
avg = c.fetchone()[0]
print(f'Average violations: {avg:.1f}' if avg else 'Average violations: 0')
print('\nBy Domain:')
c.execute('''
    SELECT ds.domain_name, COUNT(dpf.id),
           COUNT(CASE WHEN pr.violations > 0 THEN 1 END)
    FROM drupal_site ds
    LEFT JOIN drupal_pdf_files dpf ON ds.id = dpf.drupal_site_id
    LEFT JOIN pdf_report pr ON dpf.file_hash = pr.pdf_hash
    GROUP BY ds.domain_name
''')
for domain, total, with_violations in c.fetchall():
    print(f'  {domain}: {total} PDFs, {with_violations} with issues')
conn.close()
"@
Write-Host ""
Write-Host "============================================================"
Write-Host "Output Files"
Write-Host "============================================================"
Get-ChildItem output\reports -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer } | ForEach-Object { Write-Host "  $($_.FullName)" }
Get-ChildItem output\emails  -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer -and $_.Extension -eq '.html' } | ForEach-Object { Write-Host "  $($_.FullName)" }
Write-Host ""
Write-Host "Workflow complete!"
