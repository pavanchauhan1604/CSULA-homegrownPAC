import math
from jinja2 import Environment, FileSystemLoader
import os
import sys

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data_management.data_export import get_all_sites, get_pdf_reports_by_site_name
import sqlite3

# Setup Jinja2 Environment (Global)
env = Environment(loader=FileSystemLoader('.'))

def get_all_pdf_stats():
    """
    Reads the SQL query from 'sql/all_pdf_stats.sql' and executes it against the 'drupal_pdfs.db' database.
    Returns a dictionary containing overall PDF statistics:
      - total_pdf_instances
      - total_unique_pdfs
      - total_high_priority
    """
    # Open and read the SQL query from file.
    with open("sql/sum_all_pdf_stats.sql", "r") as file:
        query = file.read()

    # Connect to the SQLite database.
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()

    # Execute the SQL query.
    cursor.execute(query)

    # Fetch the single row result.
    row = cursor.fetchone()

    # Extract column names from the cursor description.
    col_names = [desc[0] for desc in cursor.description]

    # Create a dictionary mapping column names to their corresponding values.
    stats = dict(zip(col_names, row))

    print("SSSS", stats)
    # Close the database connection.
    conn.close()

    return stats

def get_all_sites_with_pdfs():
    """
    Reads the SQL query from 'sql/get_all_sites_with_pdfs.sql' and executes it against the 'drupal_pdfs.db' database.
    Returns a list of dictionaries with each site's domain name and the PDF count.
    """
    with open("sql/get_all_sites_with_pdfs.sql", "r") as file:
        query = file.read()

    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]
    sites_with_pdfs = [dict(zip(col_names, row)) for row in rows]
    conn.close()

    return sites_with_pdfs

# Example usage:
# stats = get_all_pdf_stats()
# sites_with_pdfs = get_all_sites_with_pdfs()


def fetch_sites():
    """Fetch and return the list of sites."""
    return get_all_sites()

def fetch_pdf_reports():
    """Fetch all PDF accessibility reports for each site."""
    site_pdf_reports = {}

    all_sites = fetch_sites()
    for site in all_sites:
        site_pdf_reports[site] = get_pdf_reports_by_site_name(site)

    return site_pdf_reports

def is_high_priority(data):
    """Determine if a PDF requires review based on accessibility flags."""
    if not isinstance(data, dict):
        data = dict(data._asdict())

    if data['tagged'] == 0:
        return True
    if data['pdf_text_type'] == 'Image Only':
        return True
    if data['approved_pdf_exporter']:
        return False
    if int(data['page_count']) > 0 and round(int(data['failed_checks']) / int(data['page_count'])) > 20:
        return True
    if data['has_form'] == 1 and int(data['page_count']) > 0 and round(int(data['failed_checks']) / int(data['page_count'])) > 3:
        return True
    return False

def sanitize_pdf_data(pdf_report):
    """Ensure all required fields have default values and check high priority status."""
    full_fingerprint = pdf_report.file_hash or "N/A"
    truncated_fingerprint = full_fingerprint[:7]  # First 7 characters only

    # Calculate errors per page by rounding up, if page_count is greater than 0
    if int(pdf_report.page_count) > 0:
        errors_per_page = math.ceil(int(pdf_report.failed_checks) / int(pdf_report.page_count))
    else:
        errors_per_page = "N/A"

    return {
        "pdf_uri": pdf_report.pdf_uri or "",
        "parent_uri": pdf_report.parent_uri or "",
        "scanned_date": pdf_report.scanned_date.split(" ")[0] or "N/A",
        "failed_checks": pdf_report.failed_checks or 0,
        "tagged": pdf_report.tagged or 0,
        "pdf_text_type": pdf_report.pdf_text_type or "Unknown",
        "language_set": pdf_report.language_set or 0,
        "page_count": pdf_report.page_count or 0,
        "has_form": pdf_report.has_form or 0,
        "approved_pdf_exporter": pdf_report.approved_pdf_exporter or 0,
        "file_hash": truncated_fingerprint,  # Display shortened hash
        "full_file_hash": full_fingerprint,  # Full hash for tooltip
        "high_priority": is_high_priority(pdf_report),  # Add priority flag
        "errors_per_page": errors_per_page # Precomputed errors/page value

    }

def generate_site_details():
    """Generate site details including only PDF conformance data."""
    site_pdf_reports = fetch_pdf_reports()

    site_details = {}

    for site, pdf_reports in site_pdf_reports.items():
        sanitized_reports = [sanitize_pdf_data(pdf) for pdf in pdf_reports]
        site_details[site] = {
            "pdf_reports": sanitized_reports
        }

    return site_details

def compute_metrics(site_details):
    """Compute various metrics for the report."""
    total_pdfs = 0
    total_failing = 0
    site_failures = {}

    for site, details in site_details.items():
        print(site)

        pdfs = details["pdf_reports"]

        total_pdfs += len(pdfs)
        print(total_pdfs)
        failing_count = 0
        for pdf in pdfs:
            # Count a PDF as failing if errors_per_page is an integer and > 0.
            if is_high_priority(pdf):
                failing_count += 1
        total_failing += failing_count
        site_failures[site] = failing_count

    # Sort sites by the number of failing PDFs and take the top 20.
    top_20_sites = sorted(site_failures.items(), key=lambda x: x[1], reverse=True)[:20]



    return {
        "total_pdfs": total_pdfs,
        "total_failing": total_failing,
        "top_20_sites": top_20_sites
    }



def render_template(template_name, context):
    """Load and render the Jinja2 template with the provided context."""
    template = env.get_template(template_name)
    return template.render(context)

def save_html(content, filename="output.html"):
    """Save rendered HTML content to a file."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Rendered HTML saved to {filename}")

def main():
    """Main function to orchestrate fetching data, computing metrics, rendering, and saving."""
    all_sites = fetch_sites()
    site_details = generate_site_details()


    metrics = compute_metrics(site_details)
    stats = get_all_pdf_stats()  # Get overall PDF statistics from the SQL query
    site_pdf_counts = get_all_sites_with_pdfs()  # Get sites with their respective PDF counts

    # Context for the template, including our new 'stats' and 'site_pdf_counts' data.

    print(metrics)
    print(stats)
    context = {
        "title": "Website Accessibility Report",
        "sites": all_sites,
        "site_details": site_details,
        "metrics": metrics,
        "stats": stats,
        "site_pdf_counts": site_pdf_counts,
        "scan_month": "September 2025"
    }

    # Render the template
    rendered_html = render_template("monthly_report.html", context)

    # Save the rendered HTML
    save_html(rendered_html, 'Drupal-PDF-Accessibility-Report-September-2025.html')

if __name__ == "__main__":
    main()


