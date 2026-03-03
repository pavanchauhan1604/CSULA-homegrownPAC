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

# Backup existing database (single overwriting backup in temp/)
if (Test-Path "drupal_pdfs.db") {
    if (-not (Test-Path "temp")) { New-Item -ItemType Directory -Path "temp" | Out-Null }
    Copy-Item "drupal_pdfs.db" "temp\drupal_pdfs.db.backup" -Force
    Write-Host "Backed up database to temp\drupal_pdfs.db.backup"
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

# Recreate email template
Write-Host "Recreating email template..."
$emailTemplate = @'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PDF Accessibility Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #003262;
            border-bottom: 3px solid #C4820E;
            padding-bottom: 10px;
        }}
        .greeting {{
            font-size: 16px;
            margin: 20px 0;
        }}
        .content {{
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        th {{
            background-color: #003262;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 14px;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1>PDF Accessibility Report - Cal State LA</h1>
    
    <div class="greeting">
        <p>Dear {employee_first_name},</p>
    </div>
    
    <div class="content">
        <p>This is your PDF accessibility compliance report for files associated with your Cal State LA websites.</p>
        
        <p>The following table shows PDFs that require accessibility remediation:</p>
        
        {pdf_data_table}
        
        <p>Please review these files and take action to ensure they meet accessibility standards. If you have any questions or need assistance, please contact the Office of Equity, Diversity, and Inclusion.</p>
    </div>
    
    <div class="footer">
        <p><strong>Important:</strong> This is an automated report. All PDF files on Cal State LA websites must be accessible to comply with federal and state accessibility requirements.</p>
        <p>For more information about PDF accessibility, visit: <a href="https://www.calstatela.edu/accessibility">www.calstatela.edu/accessibility</a></p>
    </div>
</body>
</html>
'@
[System.IO.File]::WriteAllText((Join-Path (Get-Location) "output\email_templates\email_template.html"), $emailTemplate, [System.Text.Encoding]::UTF8)
Write-Host "[OK] Email template recreated."

Write-Host ""
Write-Host "============================================================"
Write-Host "Fresh start complete. Run run_workflow_smooth.ps1 to begin."
Write-Host "============================================================"
