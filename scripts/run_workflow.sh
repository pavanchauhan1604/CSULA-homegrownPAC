#!/bin/bash
# Complete PDF Accessibility Workflow for CSULA
# Run this script to execute the entire workflow step by step

set -e  # Exit on error

echo "============================================================"
echo "🚀 CSULA PDF Accessibility Checker - Complete Workflow"
echo "============================================================"
echo ""

# Change to project directory
cd /Users/pavan/Work/CSULA-homegrownPAC

echo "📍 Current directory: $(pwd)"
echo ""

# Step 0: Setup Database
echo "============================================================"
echo "STEP 0: Setup Database and Load Test Data"
echo "============================================================"
echo "Command: python3 scripts/setup_test_environment.py"
echo ""
python3 scripts/setup_test_environment.py
echo ""
read -p "✓ Step 0 complete. Press Enter to continue to Step 1..."
echo ""

# Step 1: Generate Spiders
echo "============================================================"
echo "STEP 1: Generate Spiders for Test Domains"
echo "============================================================"
echo "Command: python3 config/generate_spiders.py"
echo ""
python3 config/generate_spiders.py
echo ""
read -p "✓ Step 1 complete. Press Enter to continue to Step 2..."
echo ""

# Step 2: Run Spiders
echo "============================================================"
echo "STEP 2: Crawl Websites to Find PDFs"
echo "============================================================"
echo "Command: cd crawlers/sf_state_pdf_scan && python3 run_all_spiders.py"
echo ""
echo "⏱️  This will take 5-15 minutes. Watch for crawling progress..."
echo ""
cd crawlers/sf_state_pdf_scan
python3 run_all_spiders.py
cd ../..
echo ""
read -p "✓ Step 2 complete. Press Enter to continue to Step 3..."
echo ""

# Step 3: Check what was found
echo "============================================================"
echo "STEP 3: Check Crawl Results"
echo "============================================================"
echo "Command: find output/scans -name 'scanned_pdfs.txt' -exec wc -l {} +"
echo ""
find output/scans -name 'scanned_pdfs.txt' -exec wc -l {} +
echo ""
read -p "✓ Step 3 complete. Press Enter to continue to Step 4..."
echo ""

# Step 4: Analyze PDFs
echo "============================================================"
echo "STEP 4: Analyze PDFs for Accessibility"
echo "============================================================"
echo "Command: python3 master_functions.py (running create_all_pdf_reports)"
echo ""
echo "⏱️  This will take 30-60 minutes depending on number of PDFs..."
echo ""
python3 -c "
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
read -p "✓ Step 4 complete. Press Enter to continue to Step 5..."
echo ""

# Step 5: Generate Excel Reports
echo "============================================================"
echo "STEP 5: Generate Excel Reports"
echo "============================================================"
echo "Command: python3 (running build_all_xcel_reports)"
echo ""
python3 -c "
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
read -p "✓ Step 5 complete. Press Enter to continue to Step 6..."
echo ""

# Step 6: Generate Email Reports
echo "============================================================"
echo "STEP 6: Generate Email Reports"
echo "============================================================"
echo "Command: python3 (running build_emails)"
echo ""
python3 -c "
import sys
import os
sys.path.insert(0, 'src/communication')

print('Importing modules...')
from communications import build_emails

print('Generating email reports...')
emails = build_emails()

os.makedirs('output/emails', exist_ok=True)
for email_html, recipient in emails:
    filename = f'output/emails/email_{recipient.replace(\"@\", \"_at_\").replace(\".\", \"_\")}.html'
    with open(filename, 'w') as f:
        f.write(email_html)
    print(f'  ✓ Saved: {filename}')

print('Email reports complete!')
"
echo ""
read -p "✓ Step 6 complete. Press Enter to see final results..."
echo ""

# Step 7: Display Results
echo "============================================================"
echo "STEP 7: Results Summary"
echo "============================================================"
echo ""
python3 -c "
import sqlite3
conn = sqlite3.connect('drupal_pdfs.db')
c = conn.cursor()

print('📊 Results Summary')
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
echo "📁 Output Files"
echo "============================================================"
echo ""
echo "Excel Reports:"
ls -lh output/scans/*/*.xlsx 2>/dev/null || echo "  (No Excel files found yet)"
echo ""
echo "Email Reports:"
ls -lh output/emails/*.html 2>/dev/null || echo "  (No email files found yet)"
echo ""
echo "============================================================"
echo "✅ Workflow Complete!"
echo "============================================================"
echo ""
echo " Final Summary"
echo "============================================================"
echo ""
echo "✅ Reports generated:"
echo "  • Excel Reports: output/scans/*/*.xlsx"
echo "  • Email Reports: output/emails/*.html"
echo ""
echo "💡 Next steps:"
echo "  • Open Excel: open output/scans/*/*.xlsx"
echo "  • Preview email: open output/emails/*.html"
echo "  • Verify results, then send emails: python3 scripts/send_emails.py"
echo "  • Query database: sqlite3 drupal_pdfs.db"
echo ""
