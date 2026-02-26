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
#   5. Installs VeraPDF if not already present and updates config.py
#   6. Auto-detects Teams OneDrive path and updates config.py
#   7. Prints any remaining manual configuration steps
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
# 5. VeraPDF - install if missing, then update config.py
# ---------------------------------------------------------------------------
$veraDefaultDir = "$env:USERPROFILE\veraPDF"
$veraBat = "$veraDefaultDir\verapdf.bat"
$veraConfigured = $false

if (Test-Path $veraBat) {
    Write-Host "[OK] VeraPDF already installed at: $veraBat" -ForegroundColor Green
    $veraConfigured = $true
} else {
    Write-Host "[ ] VeraPDF not found. Checking for Java..." -ForegroundColor Cyan
    $javaCmd = Get-Command java -ErrorAction SilentlyContinue
    if (-not $javaCmd) {
        Write-Host "[WARN] Java not found in PATH. VeraPDF requires Java 11+." -ForegroundColor Yellow
        Write-Host "       Install Java from https://adoptium.net/ then re-run setup.ps1" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] Java found: $($javaCmd.Source)" -ForegroundColor Green
        Write-Host "[ ] Fetching latest VeraPDF release from GitHub..." -ForegroundColor Cyan
        try {
            $releaseInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/veraPDF/veraPDF-apps/releases/latest"
            $asset = $releaseInfo.assets | Where-Object { $_.name -match "\.exe$" } | Select-Object -First 1
            if ($asset) {
                $installerPath = "$env:TEMP\$($asset.name)"
                Write-Host "[ ] Downloading $($asset.name)..." -ForegroundColor Cyan
                Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $installerPath -UseBasicParsing
                Write-Host "[OK] Download complete." -ForegroundColor Green
                Write-Host "[ ] Launching VeraPDF installer. Accept the defaults and click Next/Finish." -ForegroundColor Yellow
                Start-Process -FilePath $installerPath -Wait
                if (Test-Path $veraBat) {
                    Write-Host "[OK] VeraPDF installed at: $veraBat" -ForegroundColor Green
                    $veraConfigured = $true
                } else {
                    Write-Host "[WARN] verapdf.bat not found at expected location after install." -ForegroundColor Yellow
                    Write-Host "       If you changed the install path, update VERAPDF_COMMAND in config.py manually." -ForegroundColor Yellow
                }
            } else {
                Write-Host "[WARN] Could not find a VeraPDF .exe installer in the latest GitHub release." -ForegroundColor Yellow
                Write-Host "       Download manually from https://verapdf.org/software/" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[WARN] Failed to fetch VeraPDF release info: $_" -ForegroundColor Yellow
            Write-Host "       Download manually from https://verapdf.org/software/" -ForegroundColor Yellow
        }
    }
}

# Update VERAPDF_COMMAND in config.py if verapdf.bat is present
if (Test-Path $veraBat) {
    $configPath = (Resolve-Path ".\config.py").Path
    $configContent = Get-Content $configPath -Raw
    $newVeraLine = 'VERAPDF_COMMAND = r"' + $veraBat + '"'
    $updatedContent = $configContent -replace 'VERAPDF_COMMAND\s*=\s*r?"[^"]*"', $newVeraLine
    if ($updatedContent -ne $configContent) {
        [System.IO.File]::WriteAllText($configPath, $updatedContent, [System.Text.Encoding]::UTF8)
        Write-Host "[OK] Updated VERAPDF_COMMAND in config.py" -ForegroundColor Green
    } else {
        Write-Host "[OK] VERAPDF_COMMAND already up to date." -ForegroundColor Green
    }
    $veraConfigured = $true
}

# ---------------------------------------------------------------------------
# 6. Auto-detect Teams OneDrive path and update config.py
# ---------------------------------------------------------------------------
$oneDriveBase = "$env:USERPROFILE\OneDrive - Cal State LA"
$teamsFolderName = "PDF Accessibility Checker (PAC) - General"
$teamsPath = "$oneDriveBase\$teamsFolderName"
$teamsDetected = $false

if (Test-Path $teamsPath) {
    $configPath = (Resolve-Path ".\config.py").Path
    $configContent = Get-Content $configPath -Raw
    $newTeamsLine = 'TEAMS_ONEDRIVE_PATH = r"' + $teamsPath + '"'
    $updatedContent = $configContent -replace 'TEAMS_ONEDRIVE_PATH\s*=\s*r?"[^"]*"', $newTeamsLine
    if ($updatedContent -ne $configContent) {
        [System.IO.File]::WriteAllText($configPath, $updatedContent, [System.Text.Encoding]::UTF8)
        Write-Host "[OK] Auto-detected and updated TEAMS_ONEDRIVE_PATH in config.py" -ForegroundColor Green
    } else {
        Write-Host "[OK] TEAMS_ONEDRIVE_PATH already set correctly." -ForegroundColor Green
    }
    $teamsDetected = $true
} else {
    Write-Host "[WARN] Teams OneDrive folder not found at expected path:" -ForegroundColor Yellow
    Write-Host "       $teamsPath" -ForegroundColor Gray
    Write-Host "       Make sure OneDrive is signed in and the Teams channel is synced." -ForegroundColor Gray
}

# ---------------------------------------------------------------------------
# 7. Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Yellow
Write-Host "  Setup Summary" -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Yellow
Write-Host ""

if (-not $veraConfigured) {
    Write-Host "  [!] VeraPDF not configured" -ForegroundColor Red
    Write-Host "      Install VeraPDF from https://verapdf.org/software/" -ForegroundColor Gray
    Write-Host "      then update VERAPDF_COMMAND in config.py" -ForegroundColor Gray
    Write-Host ""
}
if (-not $teamsDetected) {
    Write-Host "  [!] TEAMS_ONEDRIVE_PATH not configured" -ForegroundColor Red
    Write-Host "      Sign in to OneDrive and sync the Teams channel, then re-run setup.ps1" -ForegroundColor Gray
    Write-Host "      Expected path: $teamsPath" -ForegroundColor Gray
    Write-Host ""
}
if ($veraConfigured -and $teamsDetected) {
    Write-Host "  All configuration complete! Ready to run." -ForegroundColor Green
    Write-Host ""
}

Write-Host "=====================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Setup complete! To activate the environment:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
