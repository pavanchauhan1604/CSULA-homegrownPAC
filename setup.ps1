# =============================================================================
# CSULA HomegrownPAC - Setup Script (Windows / PowerShell)
# =============================================================================
# Usage:  cd to the project root, then run:
#   .\setup.ps1
#
# What this does:
#   1. Verifies Python 3.11+
#   2. Creates a .venv virtual environment in the project directory
#   3. Installs all dependencies from requirements.txt
#   4. Creates any missing output/temp directories
#   5. Prints the config values you must edit before running
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  CSULA HomegrownPAC - Setup" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Check Python
# ---------------------------------------------------------------------------
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python not found in PATH." -ForegroundColor Red
    Write-Host "        Install Python 3.11+ from https://www.python.org/ and make sure" -ForegroundColor Red
    Write-Host "        'Add python.exe to PATH' is checked during installation." -ForegroundColor Red
    exit 1
}

$versionString = (python --version 2>&1).ToString().Trim()
Write-Host "[OK] Found $versionString" -ForegroundColor Green

$versionMatch = $versionString -match 'Python (\d+)\.(\d+)'
if ($versionMatch) {
    $major = [int]($Matches[1])
    $minor = [int]($Matches[2])
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
        Write-Host "[ERROR] Python 3.11+ is required. Found $versionString." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[WARN] Could not parse Python version. Continuing anyway..." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# 2. Create virtual environment
# ---------------------------------------------------------------------------
if (Test-Path ".venv") {
    Write-Host "[OK] .venv already exists - skipping creation." -ForegroundColor Green
} else {
    Write-Host "[ ] Creating virtual environment in .venv ..." -ForegroundColor Cyan
    python -m venv .venv
    Write-Host "[OK] .venv created." -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 3. Install/upgrade requirements
# ---------------------------------------------------------------------------
Write-Host "[ ] Installing requirements from requirements.txt ..." -ForegroundColor Cyan
& .\.venv\Scripts\pip install --upgrade pip --quiet
& .\.venv\Scripts\pip install -r requirements.txt
Write-Host "[OK] Requirements installed." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 4. Create missing output/temp directories
#    (config.py also does this on import, but good to have up front)
# ---------------------------------------------------------------------------
$dirs = @(
    "output\reports",
    "output\emails\sent",
    "output\emails\outlook_msg",
    "output\backups",
    "output\scans",
    "output\logs",
    "temp"
)
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "[OK] Created directory: $dir" -ForegroundColor Green
    }
}

# ---------------------------------------------------------------------------
# 5. Print manual configuration reminders
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Yellow
Write-Host "  ACTION REQUIRED - Edit config.py before running" -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. TEAMS_ONEDRIVE_PATH" -ForegroundColor White
Write-Host "     Set this to the local OneDrive path where your Teams" -ForegroundColor Gray
Write-Host "     channel Files are synced on this machine." -ForegroundColor Gray
Write-Host "     Open File Explorer -> OneDrive - Cal State LA -> find" -ForegroundColor Gray
Write-Host "     the 'PDF Accessibility Checker (PAC) - General' folder" -ForegroundColor Gray
Write-Host "     and paste the full path." -ForegroundColor Gray
Write-Host ""
Write-Host "  2. VERAPDF_COMMAND" -ForegroundColor White
Write-Host "     Set this to the full path of verapdf.bat on this machine." -ForegroundColor Gray
Write-Host "     Default install location: C:\Users\<username>\veraPDF\verapdf.bat" -ForegroundColor Gray
Write-Host "     Download VeraPDF from: https://verapdf.org/software/" -ForegroundColor Gray
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Setup complete! To activate the environment:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
