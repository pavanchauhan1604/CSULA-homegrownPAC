import os
import sqlite3
import sys

import time
from urllib.parse import urlparse, urlunparse, quote

import requests
import subprocess
import urllib3

# Disable SSL warnings for certificates we can't verify
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data_management.data_export import get_all_sites, get_pdf_reports_by_site_name
from src.data_management.data_import import add_pdf_file_to_database, get_site_id_by_domain_name, check_if_pdf_report_exists, \
    add_pdf_report_failure
from src.core.pdf_priority import violation_counter, pdf_check, pdf_status
from crawlers.sf_state_pdf_scan.sf_state_pdf_scan.box_handler import box_share_pattern_match, download_from_box
import config

temp_pdf_path = str(config.TEMP_PDF_PATH)
temp_profile_path = str(config.TEMP_PROFILE_PATH)

def download_pdf_into_memory(url, loc, domain_id):

    try:
        # Disable SSL verification for problematic certificates
        request = requests.get(url, verify=False, timeout=30)
        if request.ok:
            return request.content
        else:
            add_pdf_report_failure(url, loc, domain_id, f"Couldn't download {request.status_code}")
            return False
    except requests.exceptions.SSLError as e:
        print(f"SSL Error for {url}: {e}")
        add_pdf_report_failure(url, loc, domain_id, f"SSL certificate error")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Request error for {url}: {e}")
        add_pdf_report_failure(url, loc, domain_id, f"Download failed: {str(e)[:100]}")
        return False


def create_verapdf_report(url):

    try:
        # Use configured VeraPDF command
        verapdf_cmd = config.VERAPDF_COMMAND if hasattr(config, 'VERAPDF_COMMAND') else 'verapdf'
        
        # Construct command with proper quoting
        verapdf_command = f'"{verapdf_cmd}" -f ua1 --format json "{temp_pdf_path}" > "{temp_profile_path}"'

        # Execute the command and capture the output
        try:
            subprocess.run(verapdf_command, shell=True, text=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print("Failed to create report", url, e)
            print(e.output)

        violations = violation_counter(temp_profile_path)
        violations.update(pdf_check(temp_pdf_path))
        return {"report": {"report": violations, "status": "Succeeded"}}
    except KeyError as e:
        print("Failed to create report", url, e)
        return {"report": {"report": "", "status": "Failed"}}



def load_text_file_lines(file_path):
    with open(file_path) as f:
        return f.read().splitlines()


def loop_through_files_in_folder(folder_path):
    file_path = os.path.join(folder_path, "scanned_pdfs.txt")
    if os.path.exists(file_path):
        return load_text_file_lines(file_path)
    return None  # Return None if the file does not exist


def scan_pdfs(directory, domain_id):

    """
    Scans PDF files listed in text files within a specified directory and generates accessibility reports.

    Parameters:
    directory (str): The path to the directory containing text files with PDF URLs and their locations.
    domain_id (int): The ID of the domain associated with the PDFs.

    Process:
    1. Loads the list of PDF URLs and their locations from text files in the specified directory.
    2. For each PDF URL and location:
        a. Checks if an accessibility report already exists for the PDF.
        b. If no report exists, downloads the PDF.
        c. Generates an accessibility report using VeraPDF.
        d. Adds the report to the database if successful, or logs a failure if not.
    """

    pdf_locations = loop_through_files_in_folder(directory)
    
    # Track analyzed PDFs in this session to avoid re-analyzing the same PDF
    analyzed_pdfs_in_session = set()

    if pdf_locations:

        for file in pdf_locations:
            print("DFD", file)

            try:
                file_split = file.split(' ', 1)  # Splits at the last space

                file_url = file_split[0]
                loc = file_split[1].split(" ")[0]
                print("checking", file_url, loc)

                # Check if we already analyzed this PDF URL in this session
                if file_url in analyzed_pdfs_in_session:
                    print(f"Already analyzed in this session, skipping: {file_url}")
                    # Still need to add the record for this parent_uri if it doesn't exist
                    if not check_if_pdf_report_exists(file_url, loc):
                        # Get the existing report data and add record for this parent_uri
                        conn = sqlite3.connect('drupal_pdfs.db')
                        cursor = conn.cursor()
                        existing_pdf = cursor.execute(
                            "SELECT file_hash FROM drupal_pdf_files WHERE pdf_uri = ? LIMIT 1",
                            (file_url,)
                        ).fetchone()
                        if existing_pdf and existing_pdf[0]:
                            # Add this pdf_uri + parent_uri combination using existing hash
                            cursor.execute("""
                                INSERT OR IGNORE INTO drupal_pdf_files (pdf_uri, parent_uri, drupal_site_id, file_hash)
                                VALUES (?, ?, ?, ?)
                            """, (file_url, loc, domain_id, existing_pdf[0]))
                            conn.commit()
                        conn.close()
                    continue

                # parsed_url = urlparse(file_url)
                # encoded_path = quote(parsed_url.path)
                # file_url = urlunparse(parsed_url._replace(path=encoded_path))
                report_exsits = check_if_pdf_report_exists(file_url, loc) # report will exist if there is a hash match
            except ValueError as e:
                add_pdf_report_failure("file_url", "loc", domain_id, "Couldn't unpack file url and location")
                continue

            if not report_exsits:
                print("Report does not exist", file_url, loc)
                if box_share_pattern_match(file_url):
                    print("Downloading File From Box")
                    box_download = download_from_box(file_url, loc, domain_id) # saved to temp_pdf_path

                    if not box_download[0]:
                        print("Box Download failed", file_url)
                        add_pdf_report_failure(file_url, loc, domain_id, box_download[1])
                else:
                    pdf_download = download_pdf_into_memory(file_url,loc, domain_id) # saved to temp_pdf_path
                    if pdf_download:

                        with open(temp_pdf_path, "wb") as f:
                            f.write(pdf_download)
                    else:
                        continue

                report = create_verapdf_report(file_url) # default looks to temp_pdf_path

                if report["report"]["status"] == "Succeeded":

                    add_pdf_file_to_database(file_url, loc, domain_id, report["report"]["report"])
                    # Mark this PDF as analyzed in this session
                    analyzed_pdfs_in_session.add(file_url)
                else:
                    add_pdf_report_failure(file_url, loc, domain_id, report["report"]["report"])

            else:
                print("Report already exists", file_url)
                # Mark as analyzed even if report exists
                analyzed_pdfs_in_session.add(file_url)
                continue


def mark_replaced_pdfs_as_removed(domain_id):

    with open("sql/update_scan_by_removing_old_duplicates.sql", "r") as file:
        query = file.read()

    formatted_query = query.format(site_name=domain_id)
    print(formatted_query)
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()
    cursor.execute(formatted_query)


def refresh_existing_pdf_reports(single_domain=None):

    # this will redownload all PDFs and regenerate reports

    def scan_pdfs_by_domain(domain):



        site_data = get_pdf_reports_by_site_name(domain)
        if site_data:
            for row in site_data:
                print(row.pdf_uri)
                if box_share_pattern_match(row.pdf_uri):
                    print("Downloading File From Box")
                    box_download = download_from_box(row.pdf_uri, 'None', "None")

                    if not box_download[0]:
                        print("Box Download failed", row.pdf_uri)
                        add_pdf_report_failure(row.pdf_uri, row.parent_uri, row.drupal_site_id, box_download[1])

                else:
                    pdf_download = download_pdf_into_memory(row.pdf_uri, row.parent_uri, row.drupal_site_id)
                    if pdf_download:
                        with open(temp_pdf_path, "wb") as f:
                            f.write(pdf_download)
                    else:
                        continue

                report = create_verapdf_report(row.pdf_uri) # default looks to temp_pdf_path

                if report["report"]["status"] == "Succeeded":
                    print("Add report to DB")
                    add_pdf_file_to_database(row.pdf_uri, row.parent_uri, row.drupal_site_id, report["report"]["report"], overwrite=True)
                else:
                    add_pdf_report_failure(row.pdf_uri, row.parent_uri, row.drupal_site_id, report["report"]["report"])




    if not single_domain:
        # refresh all sites
        all_sites_list = get_all_sites()
        print(all_sites_list)
        for domain in all_sites_list:
            scan_pdfs_by_domain(domain)
            mark_replaced_pdfs_as_removed(domain)

    if single_domain:
        #refresh single domain
        scan_pdfs_by_domain(single_domain)
        mark_replaced_pdfs_as_removed(single_domain)





def full_pdf_scan(site_folders):
    """
    Scans all subdirectories within the given directory for PDF files and generates accessibility reports.

    Parameters:
    site_folders (str): The path to the directory containing subdirectories to be scanned.

    Process:
    1. Iterates over each folder (subdirectory) within the `site_folders` directory.
    2. Retrieves the domain ID for each folder by calling `get_site_id_by_domain_name`.
    3. If a valid domain ID is found, calls the `scan_pdfs` function, passing the path to the current folder and the domain ID as arguments.
    """
    for folder in os.listdir(site_folders):

        domain_id = get_site_id_by_domain_name(folder)
        print(folder, domain_id, os.path.join(site_folders, folder))
        if domain_id is not None:
            scan_pdfs(os.path.join(site_folders, folder), domain_id)



def single_site_pdf_scan(site_folder):
    """
    Scans a single subdirectory for PDF files and generates accessibility reports.

    Parameters:
    site_folder (str): The path to the subdirectory to be scanned.

    Process:
    1. Retrieves the domain ID for the folder by calling `get_site_id_by_domain_name`.
    2. If a valid domain ID is found, calls the `scan_pdfs` function, passing the path to the folder and the domain ID as arguments.
    """
    # get last folder in site folders


    domain_id = get_site_id_by_domain_name(os.path.basename(site_folder))

    if domain_id is not None:
        scan_pdfs(site_folder, domain_id)

#
if __name__=='__main__':

    mark_replaced_pdfs_as_removed("socwork.sfsu.edu")