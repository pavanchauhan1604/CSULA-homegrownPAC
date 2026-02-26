# =============================================================================
# CSULA PDF Accessibility Checker - Send Emails (PowerShell)
# Equivalent of scripts/send_emails_smooth.sh and send_emails.sh
# =============================================================================
# Usage (from project root):
#   .\scripts\send_emails.ps1           # interactive (asks for confirmation)
#   .\scripts\send_emails.ps1 -Force    # no confirmation prompt
# =============================================================================

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$PYTHON = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
Write-Host "Starting Email Sender..."
Write-Host "Using Python: $PYTHON"

if ($Force) {
    & $PYTHON scripts\send_emails.py --force
} else {
    & $PYTHON scripts\send_emails.py
}
