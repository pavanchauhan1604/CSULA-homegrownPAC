# SQL Query Library

Reusable SQL queries for data extraction and reporting.

## Query Files

- **get_all_sites.sql**: List all registered domains
- **get_pdf_reports_by_site_name.sql**: Full PDF report for a specific site
- **get_pdfs_by_domain_name.sql**: List PDFs for a domain
- **get_all_pdfs.sql**: Complete PDF inventory
- **get_failures_by_site_id.sql**: Error log for a site
- **get_admin_contacts.sql**: List of site managers
- **get_all_users_with_pdf_files.sql**: Users with assigned PDFs
- **site_ranks.sql**: Sites ranked by PDF count
- **user_ranks.sql**: Users ranked by assignment count
- **delete_duplicates.sql**: Remove duplicate PDF entries
- **update_scan_by_removing_old_duplicates.sql**: Clean up after re-scans

## Usage

Queries are loaded and executed by functions in `src/data_management/data_export.py`.

Parameters are substituted using `.format()`:
```python
with open("sql/get_pdf_reports_by_site_name.sql", 'r') as file:
    query = file.read()
    formatted = query.format(site_name="example.csula.edu")
```
