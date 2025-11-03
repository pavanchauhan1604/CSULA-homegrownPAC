#!/bin/bash

echo "============================================================"
echo "🧹 FRESH START - Complete Clean Reset"
echo "============================================================"
echo ""

cd /Users/pavan/Work/CSULA-homegrownPAC

# Stop any running processes
echo "⏹️  Stopping any running processes..."
pkill -f "python.*master_functions" 2>/dev/null
pkill -f "scrapy" 2>/dev/null
sleep 2

# Backup existing database (just in case)
if [ -f "drupal_pdfs.db" ]; then
    echo "💾 Backing up existing database..."
    cp drupal_pdfs.db "drupal_pdfs.db.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Delete database
echo "🗑️  Deleting database..."
rm -f drupal_pdfs.db

# Clean output directories
echo "🗑️  Cleaning output directories..."
rm -rf output/scans/*
rm -rf output/emails/*.html
rm -f output/emails/email_template.html

# Clean temp files
echo "🗑️  Cleaning temp files..."
rm -rf temp/*
rm -f nohup.out workflow_output.log

# Clean crawl data
echo "🗑️  Cleaning crawl data..."
rm -rf crawlers/sf_state_pdf_scan/sf_state_pdf_scan/__pycache__
rm -rf crawlers/sf_state_pdf_scan/sf_state_pdf_scan/spiders/__pycache__
# Remove generated spider files (keep only __init__.py)
find crawlers/sf_state_pdf_scan/sf_state_pdf_scan/spiders -name '*_spider.py' -delete

# Recreate necessary directories
echo "📁 Recreating directory structure..."
mkdir -p output/scans
mkdir -p output/emails
mkdir -p output/backups
mkdir -p output/reports
mkdir -p temp

# Recreate email template
echo "📧 Creating email template..."
cat > output/emails/email_template.html << 'TEMPLATE'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PDF Accessibility Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #003262;
            border-bottom: 3px solid #C4820E;
            padding-bottom: 10px;
        }}
        .greeting {{
            font-size: 16px;
            margin: 20px 0;
        }}
        .content {{
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        th {{
            background-color: #003262;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 14px;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1>PDF Accessibility Report - Cal State LA</h1>
    
    <div class="greeting">
        <p>Dear {employee_first_name},</p>
    </div>
    
    <div class="content">
        <p>This is your PDF accessibility compliance report for files associated with your Cal State LA websites.</p>
        
        <p>The following table shows PDFs that require accessibility remediation:</p>
        
        {pdf_data_table}
        
        <p>Please review these files and take action to ensure they meet accessibility standards. If you have any questions or need assistance, please contact the Office of Equity, Diversity, and Inclusion.</p>
    </div>
    
    <div class="footer">
        <p><strong>Important:</strong> This is an automated report. All PDF files on Cal State LA websites must be accessible to comply with federal and state accessibility requirements.</p>
        <p>For more information about PDF accessibility, visit: <a href="https://www.calstatela.edu/accessibility">www.calstatela.edu/accessibility</a></p>
    </div>
</body>
</html>
TEMPLATE

echo ""
echo "============================================================"
echo "✅ Fresh Start Complete!"
echo "============================================================"
echo ""
echo "📋 What was cleaned:"
echo "   • Database deleted (backup saved)"
echo "   • All output files removed"
echo "   • Temp files cleared"
echo "   • Email template recreated"
echo ""
echo "📋 Current configuration (from config.py):"
python3 -c "import config; print(f'   • Institution: {config.INSTITUTION_DOMAIN}'); print(f'   • Test email: {config.TEST_EMAIL_RECIPIENT}'); print(f'   • Test mode: {config.USE_TEST_DOMAINS_ONLY}'); print(f'   • Test domain: {config.TEST_DOMAINS[0] if config.TEST_DOMAINS else \"None\"}')"
echo ""
echo "🚀 Ready for fresh workflow run!"
echo ""
echo "Next step: ./run_workflow.sh"
echo "============================================================"
