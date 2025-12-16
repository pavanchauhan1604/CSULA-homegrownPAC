#!/usr/bin/env python3
"""
Generate Scrapy spiders for each domain in the database.
This version doesn't require network access - it generates spiders directly from domain names.
"""
import os
import sys

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.data_management.data_import import get_all_sites_domain_names

# Spider template
spider_template = """# Generated spider
import scrapy
from datetime import datetime
import os
import re

def get_box_contents(url):
    \"\"\"
    Custom handler for Box.com links. Returns (bool, url) indicating if PDF found.
    \"\"\"
    return (False, url)  # Placeholder implementation


class {class_name}(scrapy.Spider):
    name = "{name}"
    allowed_domains = ["{domain_only}"]
    start_urls = ["https://{site_url}"]
    custom_settings = {{
        'DEPTH_LIMIT': 3,
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.25,
    }}

    def __init__(self, *args, **kwargs):
        super({class_name}, self).__init__(*args, **kwargs)
        self.output_folder = "../../output/scans/{save_folder}"
        self.pdf_links = []
        self.failed_box_links = []
        # Register spider_closed callback
        from scrapy import signals
        from scrapy.signalmanager import dispatcher
        dispatcher.connect(self.spider_closed, signal=signals.spider_closed)

    def parse(self, response):
        \"\"\"
        Main parser that extracts PDF links and follows internal links.
        \"\"\"
        # Extract all links
        for link in response.css('a::attr(href)').getall():
            absolute_url = response.urljoin(link)
            
            # Check if it's a PDF
            if absolute_url.lower().endswith('.pdf'):
                referring_page = response.url
                self.pdf_links.append((absolute_url, referring_page))
                self.logger.info('Found PDF: %s (from %s)', absolute_url, referring_page)
            
            # Check if it's a Box.com link
            elif 'box.com' in absolute_url:
                yield scrapy.Request(
                    absolute_url,
                    callback=self.parse_box,
                    dont_filter=False,
                    meta={{'history': [response.url]}}
                )
            
            # Follow internal links
            elif response.url in absolute_url or absolute_url.startswith('/'):
                yield response.follow(link, callback=self.parse)

    def parse_box(self, response):
        \"\"\"
        A custom handler for Box.com links. 
        get_box_contents(url) should return a tuple of (bool, pdf_url),
        where bool indicates if a PDF was found.
        \"\"\"
        pdf_url = get_box_contents(response.url)
        referring_page = response.meta.get('history', [None])[0]

        if pdf_url and pdf_url[0]:
            self.pdf_links.append((pdf_url[1], referring_page))
        else:
            # If no PDF was found, record this Box link as "failed" for reference
            self.failed_box_links.append((pdf_url[1] if pdf_url else response.url, referring_page))

        self.logger.info('Handling a Box.com link: %s', response.url)

    def spider_closed(self, spider):
        \"\"\"
        Called automatically when the spider finishes.
        Ensures the output folder exists, then writes discovered PDF links
        (and their referring URL) to scanned_pdfs.txt with a timestamp.
        \"\"\"
        os.makedirs(self.output_folder, exist_ok=True)
        output_file_path = os.path.join(self.output_folder, 'scanned_pdfs.txt')
        failed_box_path = os.path.join(self.output_folder, 'failed_box_links.txt')

        with open(output_file_path, 'w', encoding='utf-8') as file:
            for pdf_link, ref_url in self.pdf_links:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                file.write(f"{{pdf_link}} {{ref_url}} {{timestamp}}\\n")
                
        with open(failed_box_path, 'w', encoding='utf-8') as file:
            for pdf_link, ref_url in self.failed_box_links:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                file.write(f"{{pdf_link}} {{ref_url}} {{timestamp}}\\n")

        self.logger.info("PDF LINKS saved to %s", output_file_path)
"""


def generate_spiders():
    """Generate spider files for all domains in the database."""
    
    output_dir = os.path.join(project_root, "crawlers/sf_state_pdf_scan/sf_state_pdf_scan/spiders")
    os.makedirs(output_dir, exist_ok=True)
    
    all_sites = get_all_sites_domain_names()
    
    print(f"Generating spiders for {len(all_sites)} domains...")
    
    generated = []
    failed = []
    
    for site in all_sites:
        try:
            # Convert underscores back to slashes for URLs
            site_url = site.replace('_', '/')
            
            # Create a clean name from the domain
            # Keep underscores for file/folder naming
            base_site_name = site.replace('.', ' ').replace('-', ' ').replace('_', ' ')
            site_name_cleaned_for_class = ''.join(word.capitalize() for word in base_site_name.split())
            
            # Clean for the spider name (lowercase with underscores)
            site_name_cleaned_for_name = site.replace('.', '_').replace('-', '_').lower()
            
            # Clean for the file title (same as spider name)
            site_name_cleaned_for_file_title = site_name_cleaned_for_name
            
            # Folder name for output (keep underscores)
            save_folder = site.replace('.', '-').lower()
            
            # Extract domain only (without path) for allowed_domains
            domain_only = site_url.split('/')[0] if '/' in site_url else site_url
            
            class_name = f"{site_name_cleaned_for_class}Spider"
            
            spider_code = spider_template.format(
                class_name=class_name,
                name=f"{site_name_cleaned_for_name}_spider",
                site_url=site_url,
                domain_only=domain_only,
                save_folder=save_folder
            )
            
            file_path = os.path.join(output_dir, f"{site_name_cleaned_for_file_title}_spider.py")
            with open(file_path, 'w', encoding="utf-8") as file:
                file.write(spider_code)
            
            generated.append(site)
            print(f"  ✓ Generated spider for {site}: {os.path.basename(file_path)}")
            
        except Exception as e:
            failed.append((site, str(e)))
            print(f"  ✗ Failed to generate spider for {site}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Successfully generated: {len(generated)} spiders")
    if failed:
        print(f"  Failed: {len(failed)} spiders")
        for site, error in failed:
            print(f"    - {site}: {error}")
    print(f"{'='*60}\n")
    
    return len(generated), len(failed)


if __name__ == "__main__":
    success_count, fail_count = generate_spiders()
    sys.exit(0 if fail_count == 0 else 1)
