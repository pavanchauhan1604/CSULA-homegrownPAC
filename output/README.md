# Output Files

All generated outputs are saved in this folder.

## Subfolders

- **reports/**: Excel and HTML reports
  - Site-specific Excel files: `{domain}-{YYYY-MM-DD_HH-MM-SS}.xlsx`
  - Comprehensive HTML dashboard: `Drupal-PDF-Accessibility-Report-{Month}-{Year}.html`

- **emails/**: Saved email MSG files (if using Outlook save feature)

- **backups/**: Database backups with timestamps
  - Format: `drupal_pdfs-backup-{YYYY-MM-DD}.db`

## Cleanup

Old reports and backups can be deleted periodically to save space. Keep at least the most recent month's reports.
