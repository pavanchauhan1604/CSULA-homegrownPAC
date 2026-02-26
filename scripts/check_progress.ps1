# =============================================================================
# CSULA PDF Accessibility Checker - Check Progress (PowerShell)
# Equivalent of scripts/check_progress.sh
# =============================================================================
# Usage (from project root):
#   .\scripts\check_progress.ps1
# =============================================================================

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$PYTHON = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

Write-Host "============================================================"
Write-Host "PDF Analysis Progress Report"
Write-Host "============================================================"
Write-Host ""

& $PYTHON -c @"
import sqlite3, sys
try:
    conn = sqlite3.connect('drupal_pdfs.db')
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM drupal_pdf_files')
    total = c.fetchone()[0]
    print(f'Total PDFs found:       {total}')

    c.execute('SELECT COUNT(*) FROM pdf_report')
    analyzed = c.fetchone()[0]
    print(f'PDFs analyzed:          {analyzed}')

    if total > 0:
        pct = analyzed * 100 // total
        bar = '#' * (pct // 5) + '-' * (20 - pct // 5)
        print(f'Progress:               [{bar}] {pct}%')

    c.execute('SELECT COUNT(*) FROM pdf_report WHERE violations > 0')
    with_v = c.fetchone()[0]
    print(f'PDFs with violations:   {with_v}')

    c.execute('SELECT CAST(AVG(violations) AS INTEGER) FROM pdf_report WHERE violations > 0')
    avg = c.fetchone()[0]
    print(f'Avg violations per PDF: {avg or 0}')

    print('\nBy Domain:')
    c.execute('''
        SELECT ds.domain_name, COUNT(dpf.id),
               COUNT(CASE WHEN pr.violations > 0 THEN 1 END)
        FROM drupal_site ds
        LEFT JOIN drupal_pdf_files dpf ON ds.id = dpf.drupal_site_id
        LEFT JOIN pdf_report pr ON dpf.file_hash = pr.pdf_hash
        GROUP BY ds.domain_name
    ''')
    for domain, total_d, issues in c.fetchall():
        print(f'  {domain}: {total_d} PDFs, {issues} with issues')

    conn.close()
except Exception as e:
    print(f'Error reading database: {e}')
    sys.exit(1)
"@

Write-Host ""
Write-Host "============================================================"
Write-Host "Run this script again to see updated progress."
Write-Host "============================================================"
