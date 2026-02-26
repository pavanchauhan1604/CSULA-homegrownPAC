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
#   6. Detects an existing VeraPDF install (searches common locations) and updates config.py
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
# Helper: find the real python.exe by scanning known install locations,
# ignoring the Windows Store stub (which lives under WindowsApps\)
# ---------------------------------------------------------------------------
function Find-RealJava {
    # Recursively search all Adoptium/Temurin install locations for java.exe
    # This handles any version subfolder name (jdk-21.0.x+y-hotspot, etc.)
    $searchRoots = @(
        "$env:ProgramFiles\Eclipse Adoptium",
        "${env:ProgramFiles(x86)}\Eclipse Adoptium",
        "$env:ProgramFiles\Temurin",
        "$env:ProgramFiles\Java"
    )
    foreach ($root in $searchRoots) {
        if (Test-Path $root) {
            $found = Get-ChildItem -Path $root -Recurse -Filter "java.exe" -ErrorAction SilentlyContinue |
                     Where-Object { $_.DirectoryName -like "*\bin" } |
                     Select-Object -First 1 -ExpandProperty FullName
            if ($found) { return $found }
        }
    }
    # Check JAVA_HOME if set
    if ($env:JAVA_HOME) {
        $candidate = Join-Path $env:JAVA_HOME "bin\java.exe"
        if (Test-Path $candidate) { return $candidate }
    }
    # Fall back to PATH
    $cmd = Get-Command java -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Find-RealPython {
    $candidates = @(
        # winget / python.org per-user install (most common)
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        # system-wide install
        "$env:ProgramFiles\Python311\python.exe",
        "$env:ProgramFiles\Python312\python.exe",
        "$env:ProgramFiles\Python310\python.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }
    # Fall back to PATH, but reject the Store stub
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notlike "*WindowsApps*") { return $cmd.Source }
    return $null
}

# ---------------------------------------------------------------------------
# 1. Python 3.11+
# ---------------------------------------------------------------------------
$pythonExe = Find-RealPython
$pythonOk = $false

if ($pythonExe) {
    $versionString = ""
    try { $versionString = (& $pythonExe --version 2>&1).ToString().Trim() } catch {}
    $versionMatch = $versionString -match 'Python (\d+)\.(\d+)'
    if ($versionMatch) {
        $major = [int]($Matches[1])
        $minor = [int]($Matches[2])
        if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 11)) {
            Write-Host "[OK] Found $versionString ($pythonExe)" -ForegroundColor Green
            $pythonOk = $true
        } else {
            Write-Host "[WARN] Found $versionString but 3.11+ is required. Installing newer version..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "[OK] Found Python at $pythonExe (version check inconclusive, continuing)" -ForegroundColor Green
        $pythonOk = $true
    }
} else {
    Write-Host "[ ] Python 3.11+ not found (Windows Store stub ignored). Installing via winget..." -ForegroundColor Cyan
}

if (-not $pythonOk) {
    $installed = Install-ViaWinget -PackageId "Python.Python.3.11" -FriendlyName "Python 3.11"
    if (-not $installed) {
        Write-Host "[ERROR] Could not install Python automatically." -ForegroundColor Red
        Write-Host "        Install Python 3.11+ from https://www.python.org/ (check 'Add to PATH')." -ForegroundColor Red
        exit 1
    }
    # After winget, search install locations directly (PATH may not yet be refreshed)
    $pythonExe = Find-RealPython
    if (-not $pythonExe) {
        Write-Host "[INFO] Python installed. Close this terminal, reopen it, and re-run setup.ps1" -ForegroundColor Yellow
        exit 0
    }
    $pyVer = try { (& $pythonExe --version 2>&1).ToString().Trim() } catch { "Python 3.11" }
    Write-Host "[OK] Python installed: $pyVer ($pythonExe)" -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 2. Java 21 (required by VeraPDF)
# ---------------------------------------------------------------------------
$javaExe = Find-RealJava
if ($javaExe) {
    Write-Host "[OK] Java found: $javaExe" -ForegroundColor Green
} else {
    # Show what folders exist under Program Files to help diagnose install path issues
    $adoptiumDir = "$env:ProgramFiles\Eclipse Adoptium"
    if (Test-Path $adoptiumDir) {
        Write-Host "[DBG] Eclipse Adoptium folder found but java.exe not located inside it. Contents:" -ForegroundColor Yellow
        Get-ChildItem $adoptiumDir -Recurse -Filter "java.exe" -ErrorAction SilentlyContinue |
            ForEach-Object { Write-Host "       $($_.FullName)" -ForegroundColor Yellow }
        Write-Host "       Attempting to use any java.exe found above..." -ForegroundColor Yellow
        # Brute-force: any java.exe anywhere under Program Files\Eclipse Adoptium
        $bruteFound = Get-ChildItem -Path $adoptiumDir -Recurse -Filter "java.exe" -ErrorAction SilentlyContinue |
                      Select-Object -First 1 -ExpandProperty FullName
        if ($bruteFound) {
            $javaExe = $bruteFound
            Write-Host "[OK] Java found via brute-force search: $javaExe" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Cannot locate java.exe. Re-run setup.ps1 or install Java 21 manually from https://adoptium.net/" -ForegroundColor Red
        }
    } else {
        Write-Host "[ ] Java not found. Installing Eclipse Temurin 21..." -ForegroundColor Cyan
        $installed = Install-ViaWinget -PackageId "EclipseAdoptium.Temurin.21.JDK" -FriendlyName "Java 21 (Temurin JDK)"
        if (-not $installed) {
            Write-Host "[WARN] Could not install Java automatically." -ForegroundColor Yellow
            Write-Host "       Install Java 21 from https://adoptium.net/ then re-run setup.ps1" -ForegroundColor Yellow
        } else {
            $javaExe = Find-RealJava
            if ($javaExe) {
                Write-Host "[OK] Java installed: $javaExe" -ForegroundColor Green
            } else {
                Write-Host "[INFO] Java installed. Close this terminal, reopen it, and re-run setup.ps1" -ForegroundColor Yellow
            }
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
    # Use the resolved real python path - never rely on PATH which may still have the Store stub first
    if (-not $pythonExe) {
        Write-Host "[ERROR] Real Python path unknown. Close this terminal, reopen it, and re-run setup.ps1" -ForegroundColor Red
        exit 1
    }
    & $pythonExe -m venv .venv
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
# 6. VeraPDF - find existing install and update config.py
# ---------------------------------------------------------------------------
# Auto-installs are skipped due to IzPack permission issues on some machines.
# Instead: search all common install locations, update config.py if found,
# otherwise print a clear manual-install instruction.

function Find-VeraPDF {
    $searchRoots = @(
        "$env:LOCALAPPDATA\Programs\veraPDF",
        "$env:USERPROFILE\veraPDF",
        "$env:ProgramFiles\veraPDF",
        "${env:ProgramFiles(x86)}\veraPDF",
        "$env:LOCALAPPDATA\veraPDF"
    )
    foreach ($root in $searchRoots) {
        $candidate = Join-Path $root "verapdf.bat"
        if (Test-Path $candidate) { return $candidate }
    }
    # Brute-force: search anywhere under LOCALAPPDATA and USERPROFILE
    foreach ($base in @($env:LOCALAPPDATA, $env:USERPROFILE)) {
        $found = Get-ChildItem -Path $base -Recurse -Filter "verapdf.bat" -ErrorAction SilentlyContinue |
                 Select-Object -First 1 -ExpandProperty FullName
        if ($found) { return $found }
    }
    return $null
}

$veraBat      = Find-VeraPDF
$veraConfigured = $false

if ($veraBat) {
    Write-Host "[OK] VeraPDF found at: $veraBat" -ForegroundColor Green
    $veraConfigured = $true
} else {
    Write-Host "" 
    Write-Host "[!] VeraPDF not found. Please install it manually:" -ForegroundColor Yellow
    Write-Host "    1. Go to https://verapdf.org/software/" -ForegroundColor Cyan
    Write-Host "    2. Download the Windows installer ZIP" -ForegroundColor Cyan
    Write-Host "    3. Extract the ZIP, open the extracted folder, and run verapdf-install.bat" -ForegroundColor Cyan
    Write-Host "    4. When prompted for install location, choose a folder you own, e.g.:" -ForegroundColor Cyan
    Write-Host "       $env:LOCALAPPDATA\Programs\veraPDF" -ForegroundColor White
    Write-Host "    5. Re-run setup.ps1 — it will auto-detect the install and configure config.py" -ForegroundColor Cyan
    Write-Host ""
}

if ($veraBat) {

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
    Write-Host "      Install VeraPDF manually from https://verapdf.org/software/" -ForegroundColor Gray
    Write-Host "      Extract the ZIP, run verapdf-install.bat, then re-run setup.ps1" -ForegroundColor Gray
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
