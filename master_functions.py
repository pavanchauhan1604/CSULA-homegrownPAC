import os
import json
from datetime import datetime

from src.core.conformance_checker import full_pdf_scan, refresh_existing_pdf_reports, single_site_pdf_scan
from src.data_management.data_export import get_pdf_reports_by_site_name, get_all_sites, write_data_to_excel, get_site_failures
from src.core.filters import check_for_node, is_high_priority
from src.core.scan_refresh import refresh_status
from src.utilities.tools import mark_pdfs_as_removed
import config

pdf_sites_folder = str(config.PDF_SITES_FOLDER)
scans_output = str(config.PDF_SITES_FOLDER / "{}")


def build_all_xcel_reports():

    all_sites = get_all_sites()

    for site in all_sites:
        site_data = get_pdf_reports_by_site_name(site)
        fail_data = get_site_failures(site)

        site_folder = str(config.get_site_output_path(site))
        os.makedirs(site_folder, exist_ok=True)

        timestamp = datetime.now().strftime(config.EXCEL_REPORT_TIMESTAMP_FORMAT)
        excel_file = str(
            config.get_excel_report_path(site, timestamp=timestamp, prefer_latest=False)
        )
        write_data_to_excel(site_data, fail_data, excel_file)


def build_single_xcel_report(site_name):

        site_data = get_pdf_reports_by_site_name(site_name)
        print(site_data)
        fail_data = get_site_failures(site_name)

        site_folder = str(config.get_site_output_path(site_name))
        os.makedirs(site_folder, exist_ok=True)

        timestamp = datetime.now().strftime(config.EXCEL_REPORT_TIMESTAMP_FORMAT)
        excel_file = str(
            config.get_excel_report_path(site_name, timestamp=timestamp, prefer_latest=False)
        )
        write_data_to_excel(site_data, fail_data, excel_file)




def count_reportable_pdfs():
    total_pdfs = 0
    all_sites = get_all_sites()

    for site in all_sites:
        site_folder_name = site.replace(".", "-")
        site_data = get_pdf_reports_by_site_name(site)
        fail_data = get_site_failures(site)

        for item in site_data:
            item_list = list(item)
            if not check_for_node(item_list[1]):
                total_pdfs += 1

    return total_pdfs

def count_high_priority_pdfs():
    is_high_priority_count = 0

    all_sites = get_all_sites()
    for site in all_sites:
        site_folder_name = site.replace(".", "-")
        site_data = get_pdf_reports_by_site_name(site)
        fail_data = get_site_failures(site)
        for item in site_data:

            if not is_high_priority(item):
                is_high_priority_count += 1
    return is_high_priority_count

# def backup_database():
#
#     # copies drupal_pdfs.db from this folder to /database-backups and appends '-backup--YYYY-MM-DD' to the filename
#
#     import shutil
#     from datetime import datetime
#     db_backup_folder = "C:\\Users\\913678186\\Box\\ATI\\PDF Accessibility\\CSULA Website PDF Scans\\database-backups"
#     if not os.path.exists(db_backup_folder):
#         os.makedirs(db_backup_folder)
#     db_file = "C:\\Users\\913678186\\Box\\ATI\\PDF Accessibility\\CSULA Website PDF Scans\\drupal_pdfs.db"
#     if os.path.exists(db_file):
#


def create_all_pdf_reports():
    """
    Initiates a full PDF scan for all subdirectories within the specified folder.

    This function serves as the starting point for the PDF scan process. It performs the following steps:
    1. Calls the `full_pdf_scan` function, passing the path to the main directory containing subdirectories with PDF files to be scanned.
    2. The `full_pdf_scan` function iterates over each subdirectory within the specified folder.
    3. For each subdirectory, it retrieves the domain ID by calling the `get_site_id_by_domain_name` function.
    4. If a valid domain ID is found, it calls the `scan_pdfs` function, passing the path to the current subdirectory and the domain ID as arguments.
    5. The `scan_pdfs` function loads the list of PDF URLs and their locations from text files in the specified directory.
    6. For each PDF URL and location:
        a. Checks if an accessibility report already exists for the PDF by calling the `check_if_pdf_report_exists` function.
        b. If no report exists, downloads the PDF by calling the `download_pdf_into_memory` or `download_from_box` function.
        c. Generates an accessibility report using the `create_verapdf_report` function.
        d. Adds the report to the database by calling the `add_pdf_file_to_database` function if successful, or logs a failure by calling the `add_pdf_report_failure` function if not.

    On Mac (config.MACHINE == "mac") scanning uses per-PDF parallelism via
    ProcessPoolExecutor with cpu_count * 2 workers. Each worker handles one
    PDF (download + VeraPDF + DB write), using a process-specific temp file
    path so concurrent workers never collide on disk. Workers pull from a
    flat queue of all PDFs across all domains, so no single large domain
    can bottleneck the run. SQLite WAL mode + timeout=30 handles concurrent
    write contention.

    On Windows workers=1 is used — sequential, one PDF at a time.

    Parameters:
    None

    Returns:
    None
    """

    print("Starting full PDF scan...")

    # Determine worker count: parallel on Mac, sequential on Windows.
    if config.MACHINE == "mac":
        # Per-PDF parallelism: the pool processes individual PDFs (not domains),
        # so all workers stay busy regardless of domain size distribution.
        # 2× cpu_count for I/O-bound work (network downloads + VeraPDF waits).
        workers = (os.cpu_count() or 1) * 2
        print(f"Mac detected — per-PDF parallel scan with {workers} workers (cpu_count={os.cpu_count()})")
    else:
        workers = 1

    ##
    ## Make sure to back up the database before running this function
    ##
    scan_start = datetime.now()
    print(f"Scan started: {scan_start.strftime('%Y-%m-%d %H:%M:%S')}")

    # Import pdfs and test for accessibility
    full_pdf_scan(pdf_sites_folder, workers=workers)

    scan_end = datetime.now()
    duration = scan_end - scan_start
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    duration_human = f"{hours}h {minutes}m {seconds}s"

    timing_path = config.TEMP_DIR / "scan_timing.json"
    existing = {}
    if timing_path.exists():
        try:
            with open(timing_path) as f:
                existing = json.load(f)
        except Exception:
            pass
    timing = {
        "workflow_start": existing.get("workflow_start", scan_start.strftime("%Y-%m-%d %H:%M:%S")),
        "scan_start":     scan_start.strftime("%Y-%m-%d %H:%M:%S"),
        "scan_end":       scan_end.strftime("%Y-%m-%d %H:%M:%S"),
        "scan_duration_seconds": total_seconds,
        "scan_duration_human":   duration_human,
    }
    with open(timing_path, "w") as f:
        json.dump(timing, f, indent=2)
    print(f"Scan completed: {scan_end.strftime('%Y-%m-%d %H:%M:%S')}  |  Duration: {duration_human}")
    # remove 404s and set as 404
    refresh_status()
    # compare the pdfs in the folder to the database and mark as removed if not in the folder
    mark_pdfs_as_removed(pdf_sites_folder)
    # refresh_existing_pdf_reports - DISABLED for initial scan to prevent infinite loop
    # This function re-downloads and re-analyzes ALL PDFs in the database
    # Only enable this for periodic refreshes of already-scanned PDFs
    # refresh_existing_pdf_reports()
    print("PDF scan complete!")


def single_site_full_refresh():
    single_site_pdf_scan(r"C:\Users\913678186\Box\ATI\PDF Accessibility\CSULA Website PDF Scans\creativewriting-sfsu-edu")
    refresh_status(site="creativewriting.sfsu.edu")
    mark_pdfs_as_removed(pdf_sites_folder)
    refresh_existing_pdf_reports(single_domain="creativewriting.sfsu.edu")

if __name__=="__main__":
    create_all_pdf_reports()


# create_all_pdf_reports()
# build_all_xcel_reports()
# build_single_xcel_report("creativewriting.sfsu.edu")