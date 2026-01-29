# Generated spider
import scrapy
from datetime import datetime
import os
from urllib.parse import urlparse

def get_box_contents(url):
    """
    Custom handler for Box.com links. Returns (bool, url) indicating if PDF found.
    """
    return (False, url)  # Placeholder implementation


class CalstatelaEduHhsSpider(scrapy.Spider):
    name = "calstatela_edu_hhs_spider"
    allowed_domains = ["calstatela.edu"]
    start_urls = ['https://calstatela.edu/hhs']
    scope_path = "/hhs"
    custom_settings = {
        'DEPTH_LIMIT': 3,
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.25,
    }

    def __init__(self, *args, **kwargs):
        super(CalstatelaEduHhsSpider, self).__init__(*args, **kwargs)
        self.output_folder = "../../output/scans/calstatela-edu_hhs"
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
        def is_http_url(url: str) -> bool:
            try:
                parsed = urlparse(url)
            except Exception:
                return False
            return parsed.scheme in ("http", "https", "")

        def is_internal(url: str) -> bool:
            parsed = urlparse(url)
            if not parsed.netloc:
                return True
            return parsed.netloc.lower().endswith(self.allowed_domains[0].lower())

        def is_in_scope(url: str) -> bool:
            if not getattr(self, "scope_path", ""):
                return True
            parsed = urlparse(url)
            return parsed.path.startswith(self.scope_path)

        # Extract all links
        for link in response.css('a::attr(href)').getall():
            absolute_url = response.urljoin(link)

            if not is_http_url(absolute_url):
                continue
            
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
            
            # Follow internal links (optionally scoped)
            elif is_internal(absolute_url) and is_in_scope(absolute_url):
                yield response.follow(absolute_url, callback=self.parse)

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
