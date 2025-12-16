# Generated spider
import scrapy
from datetime import datetime
import os
import re

def get_box_contents(url):
    """
    Custom handler for Box.com links. Returns (bool, url) indicating if PDF found.
    """
    return (False, url)  # Placeholder implementation


class CalstatelaEduAccessibilitySpider(scrapy.Spider):
    name = "calstatela_edu_accessibility_spider"
    allowed_domains = ["calstatela.edu"]
    start_urls = ["https://calstatela.edu/accessibility"]
    custom_settings = {
        'DEPTH_LIMIT': 3,
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.25,
    }

    def __init__(self, *args, **kwargs):
        super(CalstatelaEduAccessibilitySpider, self).__init__(*args, **kwargs)
        self.output_folder = "../../output/scans/calstatela-edu_accessibility"
        self.pdf_links = []
        self.failed_box_links = []
        # Register spider_closed callback
        from scrapy import signals
        from scrapy.signalmanager import dispatcher
        dispatcher.connect(self.spider_closed, signal=signals.spider_closed)

    def parse(self, response):
        """
        Main parser that extracts PDF links and follows internal links.
        """
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
                    meta={'history': [response.url]}
                )
            
            # Follow internal links
            elif response.url in absolute_url or absolute_url.startswith('/'):
                yield response.follow(link, callback=self.parse)

    def parse_box(self, response):
        """
        A custom handler for Box.com links. 
        get_box_contents(url) should return a tuple of (bool, pdf_url),
        where bool indicates if a PDF was found.
        """
        pdf_url = get_box_contents(response.url)
        referring_page = response.meta.get('history', [None])[0]

        if pdf_url and pdf_url[0]:
            self.pdf_links.append((pdf_url[1], referring_page))
        else:
            # If no PDF was found, record this Box link as "failed" for reference
            self.failed_box_links.append((pdf_url[1] if pdf_url else response.url, referring_page))

        self.logger.info('Handling a Box.com link: %s', response.url)

    def spider_closed(self, spider):
        """
        Called automatically when the spider finishes.
        Ensures the output folder exists, then writes discovered PDF links
        (and their referring URL) to scanned_pdfs.txt with a timestamp.
        """
        os.makedirs(self.output_folder, exist_ok=True)
        output_file_path = os.path.join(self.output_folder, 'scanned_pdfs.txt')
        failed_box_path = os.path.join(self.output_folder, 'failed_box_links.txt')

        with open(output_file_path, 'w', encoding='utf-8') as file:
            for pdf_link, ref_url in self.pdf_links:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                file.write(f"{pdf_link} {ref_url} {timestamp}\n")
                
        with open(failed_box_path, 'w', encoding='utf-8') as file:
            for pdf_link, ref_url in self.failed_box_links:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                file.write(f"{pdf_link} {ref_url} {timestamp}\n")

        self.logger.info("PDF LINKS saved to %s", output_file_path)
