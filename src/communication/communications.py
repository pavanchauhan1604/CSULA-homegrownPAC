import sqlite3
import os
from collections import namedtuple
from pathlib import Path

from src.core.filters import is_high_priority, get_priority_level
import config


def _display_domain(domain_key: str) -> str:
    """Convert internal domain keys (e.g., 'calstatela.edu_hhs') to a user-facing label.

    We keep underscores internally for safe filenames / keys, but emails should show
    paths with slashes (e.g., 'calstatela.edu/hhs').
    """
    if not domain_key:
        return ""
    if "_" not in domain_key:
        return domain_key

    host, remainder = domain_key.split("_", 1)
    remainder = remainder.strip("_")
    if not remainder:
        return host
    # Convert any remaining underscores in the path back to slashes.
    return f"{host}/{remainder.replace('_', '/')}"


def generate_pdf_details_by_employee(employee_id):
    """
    Generate detailed PDF information for an employee.
    Returns dict with domain -> list of PDF details
    """
    user_pdfs = {}
    
    # Get all PDFs for this user
    with open('sql/get_pdfs_by_user_id.sql', 'r') as file:
        sql_query = file.read()
        formatted_query = sql_query.format(employee_id=employee_id)
        conn = sqlite3.connect("drupal_pdfs.db")
        cursor = conn.cursor()
        cursor.execute(formatted_query)
        results = cursor.fetchall()
        domains = list(set([item[4] for item in results]))

    # Get detailed PDF reports for each domain
    with open('sql/get_pdf_reports_by_site_name.sql') as pdf_reports_sql:
        sql_query = pdf_reports_sql.read()
        conn = sqlite3.connect("drupal_pdfs.db")
        cursor = conn.cursor()

        for domain in domains:
            formatted_query = sql_query.format(site_name=domain)
            cursor.execute(formatted_query)
            results = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
            Row = namedtuple('Row', col_names)
            results = [Row(*row) for row in results]

            if results:
                user_pdfs[domain] = {
                    "pdfs": [],
                    "box_folder": results[0].box_folder if hasattr(results[0], 'box_folder') else None
                }
                
                for pdf in results:
                    priority_level, color_code, priority_name = get_priority_level(pdf)
                    
                    # Extract filename from URI
                    pdf_uri = pdf.pdf_uri if hasattr(pdf, 'pdf_uri') else ""
                    filename = pdf_uri.split('/')[-1] if pdf_uri else "Unknown"
                    
                    pdf_details = {
                        "filename": filename,
                        "pdf_uri": pdf_uri,
                        "violations": pdf.violations if hasattr(pdf, 'violations') else 0,
                        "failed_checks": pdf.failed_checks if hasattr(pdf, 'failed_checks') else 0,
                        "page_count": pdf.page_count if hasattr(pdf, 'page_count') else 0,
                        "priority_level": priority_level,
                        "priority_name": priority_name,
                        "color_code": color_code,
                        "parent_uri": pdf.parent_uri if hasattr(pdf, 'parent_uri') else ""
                    }
                    user_pdfs[domain]["pdfs"].append(pdf_details)
                
                # Sort PDFs by priority (high -> medium -> low) then by violations (high to low)
                priority_order = {"high": 0, "medium": 1, "low": 2}
                user_pdfs[domain]["pdfs"].sort(
                    key=lambda x: (priority_order[x["priority_level"]], -x["violations"])
                )
                
    return user_pdfs


def create_html_email_summary(data):
    """
    Create HTML summary showing PDF counts by priority.
    Data structure: {domain: {"pdfs": [...], "box_folder": "..."}}
    """
    if not data:
        return '<p style="color: #666;">No PDFs found requiring accessibility review.</p>'
    
    html = ''
    
    for domain, domain_data in data.items():
        pdfs = domain_data.get("pdfs", [])
        if not pdfs:
            continue

        display_domain = _display_domain(domain)

        unique_count = len({p.get("pdf_uri") for p in pdfs if p.get("pdf_uri")})
            
        # Count by priority
        high_count = sum(1 for p in pdfs if p["priority_level"] == "high")
        medium_count = sum(1 for p in pdfs if p["priority_level"] == "medium")
        low_count = sum(1 for p in pdfs if p["priority_level"] == "low")
        
        # Domain summary box
        html += f'''
        <div style="margin: 20px 0; padding: 20px; background-color: #f5f5f5; border-left: 4px solid #003262; border-radius: 5px;">
            <h2 style="color: #003262; margin: 0 0 15px 0; font-size: 18px;">
                {display_domain}
            </h2>
            <div style="font-size: 16px; line-height: 1.8;">
                <p style="margin: 5px 0;"><strong>Total PDFs Found:</strong> {len(pdfs)}</p>
                <p style="margin: 5px 0;"><strong>Unique PDFs:</strong> {unique_count}</p>
                <p style="margin: 5px 0;">
                    <span style="display: inline-block; width: 20px; height: 20px; background-color: #8B0000; margin-right: 8px; vertical-align: middle;"></span>
                    <strong>High Priority:</strong> {high_count} PDFs
                </p>
                <p style="margin: 5px 0;">
                    <span style="display: inline-block; width: 20px; height: 20px; background-color: #FF8C00; margin-right: 8px; vertical-align: middle;"></span>
                    <strong>Medium Priority:</strong> {medium_count} PDFs
                </p>
                <p style="margin: 5px 0;">
                    <span style="display: inline-block; width: 20px; height: 20px; background-color: #006400; margin-right: 8px; vertical-align: middle;"></span>
                    <strong>Low Priority:</strong> {low_count} PDFs
                </p>
            </div>
        </div>
        '''
    
    return html




def template_email(data_dict):

    template_path = "output/emails/email_template.html"
    with open(template_path, "r") as file:
        email_template = file.read()
        formatted_template = email_template.format(**data_dict)
        return formatted_template



def build_emails():

    emails = []
    with open('sql/get_all_users_with_pdf_files.sql') as pdf_reports_sql:
        sql_query = pdf_reports_sql.read()
        conn = sqlite3.connect("drupal_pdfs.db")
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        for employee in results:

            pdf_details = generate_pdf_details_by_employee(employee[3])
            domains_with_pdfs = [
                domain for domain, payload in (pdf_details or {}).items()
                if payload and payload.get("pdfs")
            ]

            # One email per domain (even if recipient is the same).
            base_subject = getattr(config, "EMAIL_SUBJECT", "PDF Accessibility Report")
            for domain in domains_with_pdfs:
                per_domain_details = {domain: pdf_details[domain]}
                html_summary = create_html_email_summary(per_domain_details)

                # Collect attachment for this domain only (Excel report).
                attachments = []
                try:
                    excel_path = config.get_excel_report_path(domain)
                    if excel_path.exists():
                        attachments.append(str(excel_path))
                    else:
                        print(f"Warning: Excel report not found for {domain} at {excel_path}")
                except Exception as e:
                    print(f"Error getting Excel path for {domain}: {e}")

                subject = f"{base_subject} - {_display_domain(domain)}"

                template_values = {
                    "employee_first_name": employee[0],
                    "employee_full_name": f"{employee[0]} {employee[1]}",
                    "pdf_data_table": html_summary,
                }
                email_text = template_email(template_values)
                emails.append((email_text, employee[2], attachments, subject))
    return emails


