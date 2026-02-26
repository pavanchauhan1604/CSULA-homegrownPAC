# =============================================================================
# CSULA PDF Accessibility Checker - Fresh Start / Clean Reset (PowerShell)
# Equivalent of scripts/fresh_start.sh
# =============================================================================
# Usage (from project root):
#   .\scripts\fresh_start.ps1
# WARNING: This deletes the database, all scan output, temp files, and
#          generated spiders. Run only when you want a completely clean slate.
# =============================================================================

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$PYTHON = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

Write-Host "============================================================"
Write-Host "FRESH START - Complete Clean Reset"
Write-Host "============================================================"
Write-Host "Project root: $(Get-Location)"
Write-Host "Using Python: $PYTHON"
Write-Host ""

# Regenerate spider files before deleting DB (spider gen reads from DB)
Write-Host "Regenerating spider files..."
& $PYTHON config\generate_spiders.py
Write-Host ""

# Backup existing database
if (Test-Path "drupal_pdfs.db") {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    Copy-Item "drupal_pdfs.db" "drupal_pdfs.db.backup.$stamp"
    Write-Host "Backed up database to drupal_pdfs.db.backup.$stamp"
}

# Delete database
Write-Host "Deleting database..."
Remove-Item -Force "drupal_pdfs.db" -ErrorAction SilentlyContinue

# Clean output directories
Write-Host "Cleaning output directories..."
Get-ChildItem "output\scans"  -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem "output\emails" -Filter "*.html" -ErrorAction SilentlyContinue | Remove-Item -Force

# Clean temp files
Write-Host "Cleaning temp files..."
Get-ChildItem "temp" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Remove-Item -Force "nohup.out", "workflow_output.log" -ErrorAction SilentlyContinue

# Clean generated spiders (__pycache__ and *_spider.py files)
Write-Host "Cleaning generated spider files..."
Get-ChildItem "crawlers\sf_state_pdf_scan\sf_state_pdf_scan" -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem "crawlers\sf_state_pdf_scan\sf_state_pdf_scan\spiders" -Filter "*_spider.py" -ErrorAction SilentlyContinue | Remove-Item -Force

# Recreate necessary directories
Write-Host "Recreating directory structure..."
@("output\scans","output\emails","output\email_templates","output\backups","output\reports","temp") | ForEach-Object {
    New-Item -ItemType Directory -Path $_ -Force | Out-Null
}

Write-Host ""
Write-Host "============================================================"
Write-Host "Fresh start complete. Run run_workflow_smooth.ps1 to begin."
Write-Host "============================================================"
