# CSULA PDF Checker - Installation Guide

This guide covers everything needed to install and configure the CSULA PDF Accessibility Checker from scratch.

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] macOS, Linux, or Windows computer
- [ ] Administrator/sudo access (for installing software)
- [ ] Internet connection
- [ ] At least 2GB free disk space
- [ ] Access to Cal State LA email system

---

## 1️⃣ Install Python 3.11+

### Check Current Version
```bash
python3 --version
```

If you see `Python 3.11.0` or higher, **skip to step 2**.

### macOS Installation
```bash
# Using Homebrew (recommended)
brew install python@3.11

# Or download from python.org
# Visit: https://www.python.org/downloads/macos/
```

### Linux Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3-pip

# Fedora/RHEL
sudo dnf install python3.11 python3-pip

# Arch
sudo pacman -S python
```

### Windows Installation
1. Download from https://www.python.org/downloads/windows/
2. Run installer
3. ✅ **Check "Add Python to PATH"**
4. Click "Install Now"

### Verify Installation
```bash
python3 --version
pip3 --version
```

---

## 2️⃣ Install VeraPDF

VeraPDF is **required** for PDF accessibility analysis.

### macOS Installation
```bash
# Using Homebrew (recommended)
brew install verapdf

# Manual installation
# Download from: https://software.verapdf.org/
```

### Linux Installation
```bash
# Download installer
wget https://software.verapdf.org/releases/verapdf-installer.zip

# Extract
unzip verapdf-installer.zip

# Install
cd verapdf-greenfield-*
./verapdf-install

# Add to PATH
echo 'export PATH="$HOME/verapdf:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Windows Installation
1. Download from https://software.verapdf.org/
2. Run `verapdf-installer.exe`
3. Follow installation wizard
4. Add installation folder to system PATH:
   - Control Panel → System → Advanced → Environment Variables
   - Edit "Path" variable
   - Add: `C:\Program Files\veraPDF\`

### Verify Installation
```bash
verapdf --version
```

Should output: `veraPDF 1.28.0` or higher

---

## 3️⃣ Install Python Packages

### Recommended: Use a virtual environment

From the project root:

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Install all dependencies (one command)

This project uses `requirements.txt` at the repo root:

```bash
python -m pip install -r requirements.txt
```

Notes:
- On Windows, this installs `pywin32` automatically (required for Outlook Desktop automation).
- On macOS/Linux, `pywin32` is skipped.

### Verify Installations
```bash
python -c "import scrapy; print('Scrapy:', scrapy.__version__)"
python -c "import requests; print('Requests:', requests.__version__)"
python -c "import openpyxl; print('OpenPyXL:', openpyxl.__version__)"
python -c "import pikepdf; print('PikePDF:', pikepdf.__version__)"
```

### Troubleshooting Package Installation

#### Issue: "Permission denied"
```bash
# Solution: Use --user flag
python -m pip install --user -r requirements.txt
```

#### Issue: "Command not found: pip3"
```bash
# Solution: Use python3 -m pip
python -m pip install -r requirements.txt
```

#### Issue: "SSL: CERTIFICATE_VERIFY_FAILED"
```bash
# macOS: Install certificates
/Applications/Python\ 3.11/Install\ Certificates.command

# Or use --trusted-host
pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org scrapy
```

---

## 4️⃣ Download/Clone Project

### Option A: Git Clone (Recommended)
```bash
cd ~/Work
git clone <repository-url> CSULA-homegrownPAC
cd CSULA-homegrownPAC
```

### Option B: Download ZIP
1. Download project ZIP file
2. Extract to desired location
3. Navigate to folder:
```bash
cd /Users/pavan/Work/CSULA-homegrownPAC
```

---

## 5️⃣ Make Scripts Executable

This step is **macOS/Linux only**. Windows users can skip this and follow `setup/WINDOWS_INSTALLATION_GUIDE.md`.

```bash
cd /Users/pavan/Work/CSULA-homegrownPAC
chmod +x scripts/run_workflow.sh
chmod +x scripts/fresh_start.sh
chmod +x scripts/check_progress.sh
```

---

## 6️⃣ Configure the System

### Edit config.py

Open `config.py` in your text editor:

```bash
# Using nano
nano config.py

# Using vim
vim config.py

# Using VS Code
code config.py
```

### Essential Settings to Change

```python
# 1. Test Email (CHANGE THIS)
TEST_EMAIL_RECIPIENT = "your.email@calstatela.edu"

# 2. Test Domains (Start with 1 domain)
TEST_DOMAINS = [
    "calstatela.edu",
]

# 3. Keep test mode enabled for first run
USE_TEST_DOMAINS_ONLY = True
```

### Save and Close
- **nano:** Press `Ctrl+X`, then `Y`, then `Enter`
- **vim:** Press `Esc`, type `:wq`, press `Enter`
- **VS Code:** Press `Cmd+S` (Mac) or `Ctrl+S` (Windows/Linux)

---

## 7️⃣ Test Installation

### Verify Configuration
```bash
python3 -c "import config; config.print_config()"
```

Should display your configuration settings.

### Run Setup Test
```bash
python3 scripts/setup_test_environment.py
```

Type `yes` when prompted. Should see:
```
✅ Database tables created successfully!
✅ Created sites.csv with 1 test domains
✅ Created employees.csv with 1 test employees
```

### Verify Database
```bash
sqlite3 drupal_pdfs.db "SELECT * FROM drupal_site;"
```

Should show your test domain.

---

## 8️⃣ First Test Run

### Run Complete Workflow
```bash
./scripts/fresh_start.sh && ./scripts/run_workflow.sh
```

This will:
1. Clean any previous data
2. Set up database
3. Generate spiders
4. Crawl your test domain
5. Analyze PDFs
6. Generate reports

**Expected time:** 30-90 minutes (depending on number of PDFs)

### Monitor Progress
Open a new terminal and run:
```bash
cd /Users/pavan/Work/CSULA-homegrownPAC
./scripts/check_progress.sh
```

---

## 9️⃣ View Results

### Open Excel Report
```bash
open output/scans/*/*.xlsx
```

### Open Email Preview
```bash
open output/emails/*.html
```

### Query Database
```bash
sqlite3 drupal_pdfs.db

# Inside sqlite3:
SELECT COUNT(*) FROM drupal_pdf_files;
SELECT COUNT(*) FROM pdf_report;
.exit
```

---

## ✅ Installation Complete!

You're ready to use the CSULA PDF Accessibility Checker!

### Next Steps

1. **Read the main guide:** [Complete Setup & Run Guide](COMPLETE_SETUP_GUIDE.md)
2. **Add more domains:** Edit `TEST_DOMAINS` in `config.py`
3. **Review results:** Check Excel and email reports
4. **Set up automation:** Schedule regular scans (see main guide)

---

## 🆘 Common Installation Issues

### Issue: "Python command not found"
**Solution:** Python not installed or not in PATH
```bash
# Check if python3 works
which python3

# If not found, reinstall Python and check "Add to PATH"
```

### Issue: "verapdf: command not found"
**Solution:** VeraPDF not installed or not in PATH
```bash
# macOS
brew install verapdf

# Check PATH
echo $PATH | grep verapdf
```

### Issue: "Module not found" errors
**Solution:** Python packages not installed
```bash
# Reinstall all packages
pip3 install --upgrade scrapy requests beautifulsoup4 lxml openpyxl pikepdf pdfminer.six chardet urllib3
```

### Issue: "Permission denied" when running scripts
**Solution:** Make scripts executable
```bash
chmod +x scripts/*.sh
```

### Issue: "sqlite3: command not found"
**Solution:** SQLite not installed
```bash
# macOS (included by default, but can reinstall)
brew install sqlite3

# Linux
sudo apt install sqlite3
```

---

## 📞 Support

If you encounter issues not covered here:

1. Check the [Troubleshooting section](COMPLETE_SETUP_GUIDE.md#troubleshooting) in the main guide
2. Review error messages carefully
3. Check Python and package versions
4. Verify file permissions

---

**Installation complete? Continue to:** [Complete Setup & Run Guide](COMPLETE_SETUP_GUIDE.md)
