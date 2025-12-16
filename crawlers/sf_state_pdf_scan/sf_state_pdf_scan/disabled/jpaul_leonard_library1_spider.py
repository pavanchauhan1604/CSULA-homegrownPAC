
# -*- coding: utf-8 -*-
import os
    
import scrapy
import re
from scrapy.linkextractors import LinkExtractor
from pydispatch import dispatcher
from scrapy import signals
from datetime import datetime

from ..box_handler import get_box_contents


class JPaulLeonardLibrary1Spider(scrapy.Spider):
    name = 'jpaul_leonard_library1_spider'
    start_urls = ['https://library.sfsu.edu']
    output_folder = r'C:\Users\913678186\Box\ATI\PDF Accessibility\SF State Website PDF Scans\library-sfsu-edu'

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(JPaulLeonardLibrary1Spider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def __init__(self):
        super().__init__()
        self.matched_links = []  # Store matched links, if needed
        self.pdf_links = []      # Store PDF links as tuples (pdf_url, referrer_url)
        self.failed_box_links = []  # Store Box links that failed to resolve

    def parse(self, response):
        """
        Extracts all <a href="..."> links from the page and decides:
          - If the link is within library.sfsu.edu, follow it or store if it's a PDF.
          - If the link is a Box.com link, hand it off to parse_box_link.
        """

        # Regex for library.sfsu.edu domain (handles both http and https)
        access_url_pattern = re.compile(r'https?://library.sfsu.edu/.*', re.IGNORECASE)

        # Regex for box.com links
        box_url_pattern = re.compile(r'https?://sfsu\.box\.com/s/.*', re.IGNORECASE)

        # Regex to detect .pdf files
        pdf_pattern = re.compile(r'.*\.pdf$', re.IGNORECASE)

        # Extract all <a href="..."> attributes
        extracted_links = response.css('a::attr(href)').getall()

        for link in extracted_links:
            absolute_url = response.urljoin(link)

            # If the link is internal to library.sfsu.edu
            if access_url_pattern.match(absolute_url):
                # Check if it’s a PDF
                if pdf_pattern.match(absolute_url):
                    self.pdf_links.append((absolute_url, response.url))
                else:
                    yield response.follow(absolute_url, self.parse)

            # Otherwise, if it’s a Box.com link
            elif box_url_pattern.match(absolute_url):
                history = response.meta.get('history', [])
                history.append(response.url)
                yield response.follow(absolute_url, self.parse_box_link, meta={'history': history})

    def parse_box_link(self, response):
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
