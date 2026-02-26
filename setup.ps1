# =============================================================================
# CSULA HomegrownPAC - Setup Script (Windows / PowerShell)
# =============================================================================
# Usage:  cd to the project root, then run:
#   .\setup.ps1
#
# What this does:
#   1. Installs Python 3.11 via winget if not present
#   2. Installs Java 21 (Temurin) via winget if not present
#   3. Creates a .venv virtual environment in the project directory
#   4. Installs all dependencies from requirements.txt
#   5. Creates any missing output/temp directories
#   6. Installs VeraPDF if not already present and updates config.py
#   7. Auto-detects Teams OneDrive path and updates config.py
#   8. Prints any remaining manual configuration steps
#
# Prerequisites: Windows 10 1709+ or Windows 11 (winget is built in)
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  CSULA HomegrownPAC - Setup" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# Helper: refresh PATH in the current session after a winget install
# ---------------------------------------------------------------------------
function Update-SessionPath {
    $machinePath = [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
    $userPath    = [System.Environment]::GetEnvironmentVariable("PATH", "User")
    $env:PATH    = "$machinePath;$userPath"
}

# ---------------------------------------------------------------------------
# Helper: install a package via winget
# ---------------------------------------------------------------------------
function Install-ViaWinget {
    param(
        [string]$PackageId,
        [string]$FriendlyName
    )
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        Write-Host "[WARN] winget not found. Install $FriendlyName manually." -ForegroundColor Yellow
        return $false
    }
    Write-Host "[ ] Installing $FriendlyName via winget..." -ForegroundColor Cyan
    winget install --id $PackageId --exact --silent --accept-package-agreements --accept-source-agreements
    Update-SessionPath
    return $true
}

# ---------------------------------------------------------------------------
# 1. Python 3.11+
# ---------------------------------------------------------------------------
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
$pythonOk = $false

if ($pythonCmd) {
    $versionString = (python --version 2>&1).ToString().Trim()
    $versionMatch = $versionString -match 'Python (\d+)\.(\d+)'
    if ($versionMatch) {
        $major = [int]($Matches[1])
        $minor = [int]($Matches[2])
        if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 11)) {
            Write-Host "[OK] Found $versionString" -ForegroundColor Green
            $pythonOk = $true
        } else {
            Write-Host "[WARN] Found $versionString but 3.11+ is required. Installing newer version..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "[OK] Found Python (version unreadable, continuing)" -ForegroundColor Green
        $pythonOk = $true
    }
}

if (-not $pythonOk) {
    $installed = Install-ViaWinget -PackageId "Python.Python.3.11" -FriendlyName "Python 3.11"
    if (-not $installed) {
        Write-Host "[ERROR] Could not install Python automatically." -ForegroundColor Red
        Write-Host "        Install Python 3.11+ from https://www.python.org/ (check 'Add to PATH')." -ForegroundColor Red
        exit 1
    }
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        Write-Host "[ERROR] Python still not found in PATH after install." -ForegroundColor Red
        Write-Host "        Close this terminal, reopen it, and re-run setup.ps1" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Python installed: $((python --version 2>&1).ToString().Trim())" -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 2. Java 21 (required by VeraPDF)
# ---------------------------------------------------------------------------
$javaCmd = Get-Command java -ErrorAction SilentlyContinue
if ($javaCmd) {
    Write-Host "[OK] Java found: $($javaCmd.Source)" -ForegroundColor Green
} else {
    Write-Host "[ ] Java not found. Installing Eclipse Temurin 21..." -ForegroundColor Cyan
    $installed = Install-ViaWinget -PackageId "EclipseAdoptium.Temurin.21.JDK" -FriendlyName "Java 21 (Temurin JDK)"
    if (-not $installed) {
        Write-Host "[WARN] Could not install Java automatically." -ForegroundColor Yellow
        Write-Host "       Install Java 11+ from https://adoptium.net/ then re-run setup.ps1" -ForegroundColor Yellow
    } else {
        $javaCmd = Get-Command java -ErrorAction SilentlyContinue
        if ($javaCmd) {
            Write-Host "[OK] Java installed: $($javaCmd.Source)" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Java installed but not yet in PATH." -ForegroundColor Yellow
            Write-Host "       Close this terminal, reopen it, and re-run setup.ps1" -ForegroundColor Yellow
        }
    }
}

# ---------------------------------------------------------------------------
# 3. Create virtual environment
# ---------------------------------------------------------------------------
if (Test-Path ".venv") {
    Write-Host "[OK] .venv already exists - skipping creation." -ForegroundColor Green
} else {
    Write-Host "[ ] Creating virtual environment in .venv ..." -ForegroundColor Cyan
    python -m venv .venv
    Write-Host "[OK] .venv created." -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 4. Install/upgrade requirements
# ---------------------------------------------------------------------------
Write-Host "[ ] Installing requirements from requirements.txt ..." -ForegroundColor Cyan
& .\.venv\Scripts\pip install --upgrade pip --quiet
& .\.venv\Scripts\pip install -r requirements.txt
Write-Host "[OK] Requirements installed." -ForegroundColor Green

# ---------------------------------------------------------------------------
# 5. Create missing output/temp directories
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
# 6. VeraPDF - install if missing, then update config.py
# ---------------------------------------------------------------------------
$veraDefaultDir = "$env:USERPROFILE\veraPDF"
$veraBat = "$veraDefaultDir\verapdf.bat"
$veraConfigured = $false

if (Test-Path $veraBat) {
    Write-Host "[OK] VeraPDF already installed at: $veraBat" -ForegroundColor Green
    $veraConfigured = $true
} else {
    $javaCmd = Get-Command java -ErrorAction SilentlyContinue
    if (-not $javaCmd) {
        Write-Host "[WARN] Java not in PATH - skipping VeraPDF install. Re-run setup.ps1 after Java is available." -ForegroundColor Yellow
    } else {
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
# 7. Auto-detect Teams OneDrive path and update config.py
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
# 8. Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Yellow
Write-Host "  Setup Summary" -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Yellow
Write-Host ""

if (-not $veraConfigured) {
    Write-Host "  [!] VeraPDF not configured" -ForegroundColor Red
    Write-Host "      Re-run setup.ps1 once Java is available in PATH." -ForegroundColor Gray
    Write-Host ""
}
if (-not $teamsDetected) {
    Write-Host "  [!] TEAMS_ONEDRIVE_PATH not configured" -ForegroundColor Red
    Write-Host "      Sign in to OneDrive, sync the Teams channel, then re-run setup.ps1" -ForegroundColor Gray
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
