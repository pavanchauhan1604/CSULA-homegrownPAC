#!/usr/bin/env zsh
# =============================================================================
# CSULA PDF Accessibility Checker — Mac Workflow (Non-Interactive)
# Equivalent of scripts/run_workflow_smooth.ps1, for zsh/bash on macOS.
# =============================================================================
# Usage (from project root):
#   ./scripts/run_workflow.sh
#   ./scripts/run_workflow.sh --domain calstatela.edu_ecst
#
# --domain limits Steps 1 (spider generation) and 2 (crawl) to a single domain.
# Steps 4-5 (scan + Excel) always process the full database. Run the downstream
# scripts afterwards to sync OneDrive and generate master reports.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
DOMAIN_KEY=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --domain)
            DOMAIN_KEY="$2"
            shift 2
            ;;
        *)
            echo "Unknown flag: $1"
            echo "Usage: $0 [--domain DOMAIN_KEY]"
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
cd "$(dirname "$0")/.."
echo "Working directory: $(pwd)"

if [[ -f ".venv/bin/python" ]]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python3"
fi
echo "Using Python: $PYTHON"
if [[ -n "$DOMAIN_KEY" ]]; then
    echo "Domain filter: $DOMAIN_KEY"
fi
echo ""

# ---------------------------------------------------------------------------
# Step 0: Setup / Verify Database (non-destructive)
# ---------------------------------------------------------------------------
echo "============================================================"
echo "STEP 0: Setup/Verify Database (Non-Destructive)"
echo "============================================================"
echo "(This will NOT delete drupal_pdfs.db. Use fresh_start.sh for a clean reset.)"
echo ""
"$PYTHON" scripts/setup_test_environment.py --force --no-reset
echo ""
echo "Step 0 complete."
echo ""

# ---------------------------------------------------------------------------
# Step 1: Generate Spiders
# ---------------------------------------------------------------------------
echo "============================================================"
echo "STEP 1: Generate Spiders for Domains"
echo "============================================================"
if [[ -n "$DOMAIN_KEY" ]]; then
    "$PYTHON" config/generate_spiders.py --domain "$DOMAIN_KEY"
else
    "$PYTHON" config/generate_spiders.py
fi
echo "Step 1 complete."
echo ""

# ---------------------------------------------------------------------------
# Step 2: Run Spiders (crawl websites to discover PDFs)
# ---------------------------------------------------------------------------
echo "============================================================"
echo "STEP 2: Crawl Websites to Find PDFs"
echo "============================================================"
echo "This will take 5-15 minutes..."
echo ""
pushd crawlers/csula_pdf_scan > /dev/null
if [[ -n "$DOMAIN_KEY" ]]; then
    "../../$PYTHON" run_all_spiders.py --domain "$DOMAIN_KEY"
else
    "../../$PYTHON" run_all_spiders.py
fi
popd > /dev/null
echo ""
echo "Step 2 complete."
echo ""

# ---------------------------------------------------------------------------
# Step 3: Check Crawl Results
# ---------------------------------------------------------------------------
echo "============================================================"
echo "STEP 3: Check Crawl Results"
echo "============================================================"
find output/scans -name 'scanned_pdfs.txt' -exec wc -l {} +
echo ""
echo "Step 3 complete."
echo ""

# ---------------------------------------------------------------------------
# Step 4: Analyze PDFs for Accessibility
# ---------------------------------------------------------------------------
echo "============================================================"
echo "STEP 4: Analyze PDFs for Accessibility"
echo "============================================================"
echo "This will take 30-60 minutes depending on number of PDFs..."
echo "(Mac: parallel domain scanning is enabled automatically — see master_functions.py)"
echo ""
"$PYTHON" -c "
import sys
sys.path.insert(0, 'src/core')
sys.path.insert(0, 'src/data_management')
sys.path.insert(0, 'src/utilities')
print('Importing modules...')
from master_functions import create_all_pdf_reports
print('Starting PDF analysis...')
create_all_pdf_reports()
print('PDF analysis complete!')
"
echo ""
echo "Step 4 complete."
echo ""

# ---------------------------------------------------------------------------
# Step 5: Generate Excel Reports
# ---------------------------------------------------------------------------
echo "============================================================"
echo "STEP 5: Generate Excel Reports"
echo "============================================================"
"$PYTHON" -c "
import sys
sys.path.insert(0, 'src/data_management')
sys.path.insert(0, 'src/core')
sys.path.insert(0, 'src/reporting')
print('Importing modules...')
from master_functions import build_all_xcel_reports
print('Generating Excel reports...')
build_all_xcel_reports()
print('Excel reports complete!')
"
echo ""
echo "Step 5 complete."
echo ""

# ---------------------------------------------------------------------------
# Step 7: Results Summary
# ---------------------------------------------------------------------------
echo "============================================================"
echo "STEP 7: Results Summary"
echo "============================================================"
"$PYTHON" -c "
import sqlite3
conn = sqlite3.connect('drupal_pdfs.db')
c = conn.cursor()
print('Results Summary')
print('='*60)
c.execute('SELECT COUNT(*) FROM drupal_pdf_files')
print(f'Total PDFs found: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM pdf_report')
print(f'PDFs analyzed: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM pdf_report WHERE violations > 0')
print(f'PDFs with violations: {c.fetchone()[0]}')
c.execute('SELECT AVG(violations) FROM pdf_report WHERE violations > 0')
avg = c.fetchone()[0]
print(f'Average violations: {avg:.1f}' if avg else 'Average violations: 0')
print('\nBy Domain:')
c.execute('''
    SELECT ds.domain_name, COUNT(dpf.id),
           COUNT(CASE WHEN pr.violations > 0 THEN 1 END)
    FROM drupal_site ds
    LEFT JOIN drupal_pdf_files dpf ON ds.id = dpf.drupal_site_id
    LEFT JOIN pdf_report pr ON dpf.file_hash = pr.pdf_hash
    GROUP BY ds.domain_name
''')
for domain, total, with_violations in c.fetchall():
    print(f'  {domain}: {total} PDFs, {with_violations} with issues')
conn.close()
"
echo ""
echo "============================================================"
echo "Output Files"
echo "============================================================"
echo "Excel Reports:"
ls -lh output/scans/*/*.xlsx 2>/dev/null || echo "  (No Excel files found yet)"
echo ""
echo "============================================================"
echo "Workflow complete!"
echo "============================================================"
echo ""
echo "Next steps (run separately after reviewing Excel files):"
echo "  python scripts/sharepoint_sync.py              # sync to OneDrive + email drafts"
echo "  python scripts/historical_analysis.py          # per-domain trend dashboards"
echo "  python scripts/generate_master_report.py       # master Excel"
echo "  python scripts/generate_master_report_html.py  # master HTML dashboard"
echo "  (Email sending via send_emails.py stays on Windows — Outlook COM only)"
