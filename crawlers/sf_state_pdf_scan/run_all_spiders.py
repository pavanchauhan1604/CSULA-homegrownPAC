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
    import argparse
    parser = argparse.ArgumentParser(description="Run Scrapy spiders (restart-safe).")
    parser.add_argument(
        "--domain",
        default=None,
        metavar="DOMAIN_KEY",
        help="Limit to a single domain key, e.g. calstatela.edu_ecst. "
             "The spider name is derived using the same formula as generate_spiders.py "
             "(dots and hyphens → underscores, lower-cased, _spider suffix). "
             "Omit to run all spiders.",
    )
    args = parser.parse_args()

    # Derive the expected spider name from the domain key so we can filter the
    # spider list without depending on the generated file being loaded first.
    domain_spider_filter = None
    if args.domain:
        domain_spider_filter = (
            args.domain.replace(".", "_").replace("-", "_").lower() + "_spider"
        )
        print(f"Domain filter active — looking for spider: {domain_spider_filter}")

    settings = get_project_settings()
    process = CrawlerProcess(settings)

    loader = spiderloader.SpiderLoader.from_settings(settings)
    all_spiders = list(reversed(loader.list()))
    completed = load_completed()
    to_run = [
        name for name in all_spiders
        if name not in completed
        and (domain_spider_filter is None or name == domain_spider_filter)
    ]

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