import json
import re
import sys
import os

# Add project root to path for imports
# box_handler.py is at: CSULA-homegrownPAC/crawlers/sf_state_pdf_scan/sf_state_pdf_scan/box_handler.py
# Project root is at: CSULA-homegrownPAC/
# So we need to go up 3 directories
project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import requests
from bs4 import BeautifulSoup
import lxml
from src.data_management.data_import import add_pdf_report_failure


def get_box_contents(box_url):
    page_request = requests.get(box_url)
    print("CHECKING", box_url)
    if not page_request.ok:
        # add_pdf_report_failure(box_url, parent_uri, domain_id, f"Couldn't download {page_request.status_code}")
        return False, "Can't Access PDF"

    page_request = requests.get(box_url)

    if page_request:
        page_html = BeautifulSoup(page_request.content, features="lxml")

        page_scripts = page_html.find_all("script")
        expression = re.compile("Box\.postStreamData")
        items_expression = re.compile('"items":\[\{.*.}]')
        print(page_scripts)
        for script in page_scripts:
            if expression.search(script.text):

                clean_text = script.text.replace("'","")

                items = items_expression.search(clean_text)

                raw_string_dict = f"{{{items.group()}}}"


                json_dict = json.loads(raw_string_dict)
                for item in json_dict['items']:
                    if item['extension'] == "pdf":

                        if item["canDownload"] == False:
                            print("Box File is not downloadable")
                            return False, "Box File is not downloadable"

                        print(item)
                        print(item['name'])
                        return True, box_url, item['name']





temp_pdf_path = "C:\\Users\\913678186\\IdeaProjects\\sf_state_pdf_website_scan\\temp\\temp.pdf"

import re
import requests

def download_from_box(box_link, loc=None, domain_id=None, head=False):
    """
    Given a Box share link, either returns the direct download link (if head is True)
    or downloads the PDF to a local path (loc) if the file is found.

    Parameters:
        box_link (str): The Box share link.
        loc (str): The web location of the PDF.
        domain_id: (Unused here, but may be used for logging or further processing).
        head (bool): If True, simply returns the direct download URL without downloading.

    Returns:
        tuple: (True, download_url or empty string) on success, (False, error_message) on failure.
    """
    if not box_share_pattern_match(box_link):
        print("Not a valid box share link")
        return False, "Not a valid box share link"

    direct_download_url = "https://sfsu.app.box.com/public/static/{share_hash}.{extension}"
    share_hash = box_link.split("/")[-1]

    box_contents = get_box_contents(box_link)
    print(f"Box contents: {box_contents} for link: {box_link}")
    if box_contents is None:
        return False, ""
    if box_contents[0]:
        print("Found PDF")
        download_url = direct_download_url.format(share_hash=share_hash, extension="pdf")

        if head:
            print("Head flag is True. Returning the download link without downloading.")
            return download_url
        else:
            print(f"Downloading PDF from: {download_url}")
            file_response = requests.get(download_url, stream=True)
            # Assuming 'loc' is the file path where we want to save the PDF.

            with open(temp_pdf_path, "wb") as f:
                f.write(file_response.content)
            print(f"Downloaded PDF saved to: {temp_pdf_path}")
            return True, ""
    else:
        print("Box contents not found or error occurred.")
        return False, box_contents[1]

def box_share_pattern_match(url):
    # Pattern to match the specific domain and extract the hash.
    pattern = r'https:\/\/[a-zA-Z0-9.-]*\.box\.com\/s\/[a-zA-Z0-9]+'
    match = re.match(pattern, url)
    return True if match else False



