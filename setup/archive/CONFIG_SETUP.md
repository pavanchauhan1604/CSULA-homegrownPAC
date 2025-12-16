# Configuration Setup Guide

## Overview

The CSULA PDF Accessibility Checker now uses a centralized configuration system. All paths, settings, and parameters are defined in a single `config.py` file, making it easy to adapt the system to different environments.

## Quick Start

### 1. Review Configuration

Open `config.py` and review the settings:

```python
# Institution settings
INSTITUTION_DOMAIN = "calstatela.edu"
INSTITUTION_NAME = "Cal State LA"
ACCESSIBILITY_EMAIL = "accessibility@calstatela.edu"

# Test mode
USE_TEST_DOMAINS_ONLY = True
TEST_DOMAINS = [
    "www.calstatela.edu",
    "www-adminfin.calstatela.edu",
    "academicsenate.calstatela.edu",
]
```

### 2. Set Up Test Environment

Run the setup script to create test data:

```bash
python3 setup_test_environment.py
```

This will:
- Create the SQLite database
- Generate test CSV files with sample domains and users
- Populate the database with test data
- Display a summary of what was created

### 3. Verify Configuration

Test that the configuration is valid:

```bash
python3 config.py
```

You should see output like:
```
======================================================================
CSULA PDF Checker Configuration
======================================================================
Institution: Cal State LA
Domain: calstatela.edu
Database: /path/to/drupal_pdfs.db
...
✅ Configuration is valid!
```

## Configuration File Structure

### Key Sections

#### 1. **Institution Settings**
- `INSTITUTION_DOMAIN`: Your institution's domain (e.g., "calstatela.edu")
- `INSTITUTION_NAME`: Full institution name for reports
- `ACCESSIBILITY_EMAIL`: Email address for sending reports

#### 2. **Directory Paths**
All paths are automatically calculated relative to the project root:
- `DATA_DIR`: CSV data files
- `OUTPUT_DIR`: Generated reports and outputs
- `TEMP_DIR`: Temporary files during processing
- `SQL_DIR`: SQL query files

#### 3. **Database Settings**
- `DATABASE_PATH`: SQLite database location
- `DB_BACKUP_DIR`: Where to store database backups

#### 4. **PDF Scanning Settings**
- `PDF_SITES_FOLDER`: Root folder for scan results
- `VERAPDF_COMMAND`: Path to VeraPDF executable
- `VERAPDF_PROFILE`: Validation profile (ua1, ua2, etc.)

#### 5. **Test/Development Settings**
- `USE_TEST_DOMAINS_ONLY`: Use only test domains (True) or all domains (False)
- `TEST_DOMAINS`: List of domains for testing

## Customization Guide

### For Different Institutions

1. Update institution settings:
```python
INSTITUTION_DOMAIN = "youruniversity.edu"
INSTITUTION_NAME = "Your University"
ACCESSIBILITY_EMAIL = "access@youruniversity.edu"
```

2. Update test domains:
```python
TEST_DOMAINS = [
    "www.youruniversity.edu",
    "library.youruniversity.edu",
]
```

### For Production Use

1. Set test mode to False:
```python
USE_TEST_DOMAINS_ONLY = False
```

2. Populate `data/sites.csv` with all your domains

3. Update employee data in CSV files

### For Different Environments

#### Development Machine
```python
# Use relative paths (default)
OUTPUT_DIR = PROJECT_ROOT / "output"
```

#### Server Deployment
```python
# Use absolute paths
OUTPUT_DIR = Path("/var/www/pdf_checker/output")
PDF_SITES_FOLDER = Path("/mnt/storage/pdf_scans")
```

## Environment Variables

You can override configuration using environment variables:

```bash
export CSULA_PDF_DB_PATH="/custom/path/database.db"
export CSULA_PDF_OUTPUT_DIR="/custom/output"
```

Then in `config.py`:
```python
import os
DATABASE_PATH = Path(os.getenv("CSULA_PDF_DB_PATH", PROJECT_ROOT / "drupal_pdfs.db"))
```

## CSV Data Files

### sites.csv
Format: `domain,security_group_name`
```csv
www.calstatela.edu,CSULA-d-main-site-content-manager
library.calstatela.edu,CSULA-d-library-content-manager
```

### employees.csv
Format: `Full Name,Employee ID,Email`
```csv
Full Name,Employee ID,Email
John Doe,123456,john.doe@calstatela.edu
Jane Smith,234567,jane.smith@calstatela.edu
```

### managers.csv
Format: `Employee ID`
```csv
123456
234567
```

### site_assignments.csv
Format: `Security Group,Name,Employee ID,Email`
```csv
CSULA-d-main-site-content-manager,John Doe,123456,john.doe@calstatela.edu
CSULA-d-library-content-manager,Jane Smith,234567,jane.smith@calstatela.edu
```

## Helper Functions

The config module provides helper functions:

```python
import config

# Get domain folder name
folder = config.get_domain_folder_name("www.calstatela.edu")  
# Returns: "www-calstatela-edu"

# Get site output path
path = config.get_site_output_path("www.calstatela.edu")
# Returns: Path object to output/scans/www-calstatela-edu/

# Get Excel report path
report = config.get_excel_report_path("www.calstatela.edu")
# Returns: Path to Excel report file

# Get backup path with timestamp
backup = config.get_backup_path("database.db", timestamp=True)
# Returns: Path to output/backups/database-2025-01-15_14-30-00.db
```

## Validation

The configuration is automatically validated on import. To manually validate:

```python
import config

try:
    config.validate_config()
    print("Configuration is valid!")
except ValueError as e:
    print(f"Configuration error: {e}")
```

## Troubleshooting

### Database Not Found
If you see "Database does not exist":
1. Run `python3 setup_test_environment.py`
2. Or manually create it using `src/core/database.py`

### Path Issues
If paths are incorrect:
1. Check that you're running from the project root
2. Verify `BASE_DIR` is correct in `config.py`
3. Use absolute paths if needed

### VeraPDF Not Found
If VeraPDF command fails:
1. Install VeraPDF: https://verapdf.org/
2. Add to PATH, or set full path in config:
```python
VERAPDF_COMMAND = "/usr/local/bin/verapdf"
```

## Next Steps

After configuration:

1. **Test the setup**: Run `python3 setup_test_environment.py`
2. **Generate spiders**: Run spider generation for test domains
3. **Test scanning**: Run a single site scan
4. **Review results**: Check output directories for reports
5. **Scale up**: Add more domains and run full scans

## Support

For issues or questions:
- Check the main README.md
- Review docs/PROJECT_STRUCTURE.md
- Check the QUICKSTART.md guide
