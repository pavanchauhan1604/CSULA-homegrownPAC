# Data Files

This folder contains CSV data files for importing employees, sites, and assignments.

## Files

- **employees.csv**: Employee roster with IDs, names, and emails
- **employees1.csv**: Additional employee data
- **sites.csv**: List of Drupal domains to scan
- **site_assignments.csv**: Maps employees to their assigned sites
- **managers.csv**: List of managers/administrators

## Format

CSV files should follow these formats:

### employees.csv
```
Name,Employee_ID,Email
John Doe,12345,jdoe@csula.edu
```

### sites.csv
```
Domain,Security_Group
example.csula.edu,web-admin
```

### site_assignments.csv
```
Security_Group,Name,Employee_ID,Email
web-admin,John Doe,12345,jdoe@csula.edu
```

## Import

Run `python src/data_management/data_import.py` to import these files into the database.
