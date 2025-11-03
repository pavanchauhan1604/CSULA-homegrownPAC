import os
import sys
from pathlib import Path

# Add project root to path to import config
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy import spiderloader, signals
from pydispatch import dispatcher

COMPLETED_FILE = config.TEMP_DIR / 'completed_spiders.txt'

def load_completed():
    if not os.path.exists(COMPLETED_FILE):
        return set()
    with open(COMPLETED_FILE) as f:
        return {line.strip() for line in f if line.strip()}

def mark_completed(spider_name):
    # open/close on each call so it's flushed immediately
    with open(COMPLETED_FILE, 'a') as f:
        f.write(spider_name + '\n')

if __name__ == '__main__':
    settings = get_project_settings()
    process = CrawlerProcess(settings)

    loader = spiderloader.SpiderLoader.from_settings(settings)
    all_spiders = list(reversed(loader.list()))
    completed = load_completed()
    to_run = [name for name in all_spiders if name not in completed]

    if not to_run:
        print("All spiders have already completed. Exiting.")
        exit()

    spider_iter = iter(to_run)

    def run_next():
        try:
            name = next(spider_iter)
        except StopIteration:
            return
        print(f"Starting spider: {name}")
        process.crawl(name)

    def on_spider_closed(spider, reason):
        if reason == 'finished':
            # Immediately record the successful run
            mark_completed(spider.name)
            print(f"Recorded completion of spider: {spider.name}")
        else:
            print(f"Spider '{spider.name}' closed (reason: {reason})")
        run_next()

    dispatcher.connect(on_spider_closed, signal=signals.spider_closed)

    run_next()
    process.start()