# Configuration Quick Reference

## Common Tasks

### 1. Initial Setup (First Time)

```bash
# 1. Review and customize config.py
nano config.py  # or your preferred editor

# 2. Run test environment setup
python3 setup_test_environment.py

# 3. Verify configuration
python3 config.py
```

### 2. Switch from Test to Production

In `config.py`, change:
```python
# From:
USE_TEST_DOMAINS_ONLY = True

# To:
USE_TEST_DOMAINS_ONLY = False
```

### 3. Add New Domains

Edit `data/sites.csv`:
```csv
newdomain.calstatela.edu,CSULA-d-newdomain-content-manager
```

Then reload database:
```bash
python3 -c "from src.data_management import data_import; data_import.add_sites_from_site_csv_file('data/sites.csv')"
```

### 4. Change Output Locations

In `config.py`:
```python
# For local testing
OUTPUT_DIR = PROJECT_ROOT / "output"

# For server deployment
OUTPUT_DIR = Path("/var/www/pdf_checker/output")
```

### 5. Update Institution Settings

In `config.py`:
```python
INSTITUTION_DOMAIN = "yourcollege.edu"
INSTITUTION_NAME = "Your College Name"
ACCESSIBILITY_EMAIL = "access@yourcollege.edu"
```

### 6. Configure Email Sending

In `config.py`:
```python
# For Gmail SMTP
EMAIL_METHOD = "smtp"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your.email@gmail.com"
SMTP_PASSWORD = "your-app-password"  # Not your regular password!
```

### 7. Adjust Crawling Speed

In `config.py`:
```python
# Faster (use with caution)
DOWNLOAD_DELAY = 0.01
CONCURRENT_REQUESTS_PER_DOMAIN = 16

# Slower (more polite)
DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS_PER_DOMAIN = 2
```

### 8. Backup Database

```bash
python3 -c "import config, shutil; shutil.copy(config.DATABASE_PATH, config.get_backup_path('drupal_pdfs.db'))"
```

### 9. Reset Everything (DANGER!)

```bash
# This will delete all data!
rm -rf output/*
rm drupal_pdfs.db
python3 setup_test_environment.py
```

### 10. Check Configuration Status

```bash
python3 config.py
```

## Configuration Checklist

Before running in production:

- [ ] Updated `INSTITUTION_DOMAIN`
- [ ] Updated `INSTITUTION_NAME`
- [ ] Updated `ACCESSIBILITY_EMAIL`
- [ ] Set `USE_TEST_DOMAINS_ONLY = False`
- [ ] Populated `data/sites.csv` with all domains
- [ ] Populated `data/employees.csv` with staff
- [ ] Populated `data/site_assignments.csv`
- [ ] Tested with a few domains first
- [ ] Backed up any existing database
- [ ] VeraPDF is installed and accessible
- [ ] All output directories are writable
- [ ] Database path is correct

## Environment-Specific Settings

### Local Development
```python
USE_TEST_DOMAINS_ONLY = True
TEST_DOMAINS = ["www.example.edu", "library.example.edu"]
LOG_LEVEL = "DEBUG"
```

### Staging Server
```python
USE_TEST_DOMAINS_ONLY = False
LOG_LEVEL = "INFO"
DATABASE_PATH = Path("/data/staging/drupal_pdfs.db")
OUTPUT_DIR = Path("/data/staging/output")
```

### Production Server
```python
USE_TEST_DOMAINS_ONLY = False
LOG_LEVEL = "WARNING"
DATABASE_PATH = Path("/data/production/drupal_pdfs.db")
OUTPUT_DIR = Path("/data/production/output")
DB_BACKUP_DIR = Path("/backups/pdf_checker/database")
```

## Paths Reference

| Setting | Default | Purpose |
|---------|---------|---------|
| `BASE_DIR` | Project root | Base directory for all paths |
| `DATA_DIR` | `data/` | CSV input files |
| `OUTPUT_DIR` | `output/` | All generated files |
| `TEMP_DIR` | `temp/` | Temporary processing files |
| `SQL_DIR` | `sql/` | SQL query templates |
| `PDF_SITES_FOLDER` | `output/scans/` | Spider output folders |
| `DATABASE_PATH` | `drupal_pdfs.db` | SQLite database |

## Import Pattern

In any Python file, import config:

```python
# At the top of your file
import config

# Use configuration values
db_path = config.DATABASE_PATH
output_dir = config.OUTPUT_DIR
temp_pdf = config.TEMP_PDF_PATH

# Use helper functions
site_path = config.get_site_output_path("www.example.edu")
```

## Common Issues

### Issue: "Database does not exist"
**Solution:**
```bash
python3 setup_test_environment.py
```

### Issue: "VeraPDF command not found"
**Solution:**
```python
# In config.py, set full path:
VERAPDF_COMMAND = "/usr/local/bin/verapdf"
```

### Issue: "Permission denied on output directory"
**Solution:**
```bash
chmod -R 755 output/
# Or change OUTPUT_DIR to a writable location
```

### Issue: "Import error: cannot import config"
**Solution:**
```bash
# Make sure you're in the project root
cd /path/to/CSULA-homegrownPAC
python3 your_script.py
```

### Issue: Paths with spaces or special characters
**Solution:**
```python
# Use Path objects (they handle this automatically)
from pathlib import Path
OUTPUT_DIR = Path("/path with spaces/output")
```

## Testing Configuration

```bash
# Test configuration validity
python3 config.py

# Test database connection
python3 -c "import config, sqlite3; conn = sqlite3.connect(config.DATABASE_PATH); print('Database OK')"

# Test output directory
python3 -c "import config; config.OUTPUT_DIR.mkdir(exist_ok=True); print('Output directory OK')"

# Test VeraPDF
verapdf --version

# Test temp directory
python3 -c "import config; (config.TEMP_DIR / 'test.txt').write_text('test'); print('Temp directory OK')"
```

## Performance Tuning

### For Fast Scanning (High-Speed Networks)
```python
CONCURRENT_REQUESTS = 32
DOWNLOAD_DELAY = 0.01
CONCURRENT_REQUESTS_PER_DOMAIN = 16
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
```

### For Polite Scanning (Shared Networks)
```python
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 0.25
CONCURRENT_REQUESTS_PER_DOMAIN = 4
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
```

### For Slow Networks or Unreliable Sites
```python
CONCURRENT_REQUESTS = 4
DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS_PER_DOMAIN = 2
AUTOTHROTTLE_START_DELAY = 10
AUTOTHROTTLE_MAX_DELAY = 120
```

## Security Notes

1. **Never commit sensitive data to Git:**
   - Email passwords
   - API keys
   - Employee personal information

2. **Use environment variables for secrets:**
   ```bash
   export SMTP_PASSWORD="secret"
   ```
   ```python
   import os
   SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
   ```

3. **Restrict database permissions:**
   ```bash
   chmod 600 drupal_pdfs.db
   ```

4. **Keep backups secure:**
   ```bash
   chmod 700 output/backups/
   ```
