#!/bin/bash
# Check PDF Analysis Progress

echo "============================================================"
echo "📊 PDF Analysis Progress Report"
echo "============================================================"
echo ""

cd /Users/pavan/Work/CSULA-homegrownPAC

# Count total PDFs found
TOTAL_PDFS=$(sqlite3 drupal_pdfs.db "SELECT COUNT(*) FROM drupal_pdf_files;")
echo "Total PDFs found: $TOTAL_PDFS"

# Count PDFs analyzed
ANALYZED=$(sqlite3 drupal_pdfs.db "SELECT COUNT(*) FROM pdf_report;")
echo "PDFs analyzed: $ANALYZED"

# Calculate percentage
if [ "$TOTAL_PDFS" -gt 0 ]; then
    PERCENT=$((ANALYZED * 100 / TOTAL_PDFS))
    echo "Progress: $PERCENT%"
fi

echo ""

# Count PDFs with violations
WITH_VIOLATIONS=$(sqlite3 drupal_pdfs.db "SELECT COUNT(*) FROM pdf_report WHERE violations > 0;")
echo "PDFs with violations: $WITH_VIOLATIONS"

# Average violations
AVG=$(sqlite3 drupal_pdfs.db "SELECT CAST(AVG(violations) AS INTEGER) FROM pdf_report WHERE violations > 0;")
echo "Average violations per PDF: ${AVG:-0}"

echo ""
echo "============================================================"
echo "Run this script again to see updated progress:"
echo "  ./check_progress.sh"
echo "============================================================"
