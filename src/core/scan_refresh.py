import sqlite3
import sys
import os
import requests

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data_management.data_export import get_pdfs_by_site_name
from crawlers.sf_state_pdf_scan.sf_state_pdf_scan.box_handler import box_share_pattern_match, download_from_box

def check_box_pdf_status(pdf_uri):
    """
    For a Box share link, obtain the direct download URL and check its status.
    If the initial HEAD request returns 302, follow the 'Location' header and do another HEAD.

    Parameters:
        pdf_uri (str): The original Box share link.

    Returns:
        (bool, int or None): A tuple where the first element is True if the final response is 200,
                             and the second element is the final status code (or None if an error occurred).
    """
    download_url = download_from_box(pdf_uri, loc="", domain_id=None, head=True)
    if not isinstance(download_url, str) or not download_url:
        print(f"Failed to obtain download link for Box share: {pdf_uri}")
        return False, None

    try:
        response = requests.head(download_url, timeout=10, allow_redirects=False)
        print(f"Initial Box HEAD status for URL {download_url}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Box PDF download URL ({download_url}): {e}")
        return False, None

    if response.status_code == 302:
        new_url = response.headers.get("Location")
        if new_url:
            print(f"Following redirect to: {new_url}")
            try:
                final_response = requests.head(new_url, timeout=10)
                print(f"Final Box HEAD status for URL {new_url}: {final_response.status_code}")
                return final_response.status_code == 200, final_response.status_code
            except requests.exceptions.RequestException as e:
                print(f"Error fetching final Box PDF URL ({new_url}): {e}")
                return False, None
        else:
            print("Redirect response did not contain a Location header.")
            return False, response.status_code
    else:
        # If the status is not a redirect, check if it is 200.
        return response.status_code == 200, response.status_code

def refresh_status(box_only=False, site=None):
    """
    Loop through all PDFs and their parent URIs, making HTTP HEAD requests to check their status.
    If box_only is True, only PDF URIs that are Box share links are checked and no other URLs are processed.
    For Box share links, obtain the direct download URL using download_from_box (head=True)
    and perform the HEAD request on that URL. If a URL returns a 404 (or cannot be reached),
    set the corresponding flag in the database.

    Parameters:
        box_only (bool): If True, only check PDF URIs that are Box share links. Defaults to False.
    """
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()
    pdfs = cursor.execute("SELECT * FROM drupal_pdf_files").fetchall()

    if site:
        pdfs = get_pdfs_by_site_name(site)



    total_records = len(pdfs)
    print(f"Total records found: {total_records}")

    for i, each in enumerate(pdfs, start=1):
        pdf_id = each[0]
        pdf_uri = each[1]
        pdf_parent = each[2]

        print(f"\nProcessing record {i}/{total_records}: ID {pdf_id}")

        # Skip problematic URIs if they contain spaces (indicating possible formatting issues)
        if len(pdf_uri.split(" ")) > 1 or len(pdf_parent.split(" ")) > 1:
            print(f"Skipping problematic URIs for ID {pdf_id}: '{pdf_uri}', '{pdf_parent}'")
            continue

        if box_only:
            # Only process Box share links in box_only mode.
            if box_share_pattern_match(pdf_uri):
                print(f"PDF URI is a Box share link: {pdf_uri}")
                is_ok, status_code = check_box_pdf_status(pdf_uri)
                if not is_ok:
                    cursor.execute("UPDATE drupal_pdf_files SET pdf_returns_404 = ? WHERE id = ?", (1, pdf_id))
                else:
                    cursor.execute("UPDATE drupal_pdf_files SET pdf_returns_404 = ? WHERE id = ?", (0, pdf_id))
            else:
                print(f"Skipping non-Box PDF URI for ID {pdf_id}: {pdf_uri}")
            # In box_only mode, skip parent URL checks.
        else:
            # Process Box share links
            if box_share_pattern_match(pdf_uri):
                print(f"PDF URI is a Box share link: {pdf_uri}")
                is_ok, status_code = check_box_pdf_status(pdf_uri)
                if not is_ok:
                    cursor.execute("UPDATE drupal_pdf_files SET pdf_returns_404 = ? WHERE id = ?", (1, pdf_id))
                else:
                    cursor.execute("UPDATE drupal_pdf_files SET pdf_returns_404 = ? WHERE id = ?", (0, pdf_id))
            else:
                # Regular PDF URI check
                try:
                    print(f"Checking PDF URL: {pdf_uri}")
                    pdf_response = requests.head(pdf_uri, timeout=10)
                    print(f"PDF URL status code: {pdf_response.status_code}")
                    if pdf_response.status_code == 404:
                        cursor.execute("UPDATE drupal_pdf_files SET pdf_returns_404 = ? WHERE id = ?", (1, pdf_id))
                    else:
                        cursor.execute("UPDATE drupal_pdf_files SET pdf_returns_404 = ? WHERE id = ?", (0, pdf_id))
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching PDF URL ({pdf_uri}): {e}")
                    cursor.execute("UPDATE drupal_pdf_files SET pdf_returns_404 = ? WHERE id = ?", (1, pdf_id))

            # Check Parent URL status using HEAD request for non-box_only mode
            try:
                print(f"Checking Parent URL: {pdf_parent}")
                parent_response = requests.head(pdf_parent, timeout=10)
                print(f"Parent URL status code: {parent_response.status_code}")
                if parent_response.status_code == 404:
                    cursor.execute("UPDATE drupal_pdf_files SET parent_returns_404 = ? WHERE id = ?", (1, pdf_id))
                else:
                    cursor.execute("UPDATE drupal_pdf_files SET parent_returns_404 = ? WHERE id = ?", (0, pdf_id))
            except requests.exceptions.RequestException as e:
                print(f"Error fetching Parent URL ({pdf_parent}): {e}")
                cursor.execute("UPDATE drupal_pdf_files SET parent_returns_404 = ? WHERE id = ?", (1, pdf_id))

        print(f"Finished processing record ID {pdf_id}")

    conn.commit()
    print("\nAll records processed. Changes committed to the database.")
    conn.close()
    print("Database connection closed.")


if __name__== "__main__":
    refresh_status()
