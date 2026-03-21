import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

if __name__ == '__main__':
    # Get project settings
    settings = get_project_settings()
    process = CrawlerProcess(settings)

    # Provide the spider name you want to run
    spider_name = 'information_technology_services2_spider'  # Replace with your actual spider name

    # Schedule the spider to crawl
    process.crawl(spider_name)

    # Start the crawling process
    process.start()