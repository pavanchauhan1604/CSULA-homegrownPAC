# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy



class PdfItem(scrapy.Item):
    file_urls = scrapy.Field()  # List of file URLs for Scrapy's FilesPipeline to download
    files = scrapy.Field()      # Stores information about the downloaded files (populated by FilesPipeline)
    title = scrapy.Field()      # Optional: Title or name of the PDF
    source_url = scrapy.Field() #


class SfStatePdfScanItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass
