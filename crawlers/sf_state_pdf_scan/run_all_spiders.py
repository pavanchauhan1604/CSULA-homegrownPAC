import os
import sys
import threading
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path to import config
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from scrapy.utils.project import get_project_settings
from scrapy import spiderloader

# ---------------------------------------------------------------------------
# How many spiders to crawl simultaneously.
#
# All CSULA spiders target subpaths of calstatela.edu, so they all hit the
# same server. Each Scrapy spider already fires 16 concurrent requests
# internally, so 3 parallel spiders = ~48 simultaneous requests to the
# university server — fast enough to be meaningfully quicker than sequential,
# conservative enough to avoid rate-limiting or triggering DDoS protection.
#
# Increase to 4-5 only if the university server handles it without 429s.
# ---------------------------------------------------------------------------
MAX_CONCURRENT_SPIDERS = 3

COMPLETED_FILE = config.TEMP_DIR / "completed_spiders.txt"
SPIDER_DIR = Path(__file__).resolve().parent   # crawlers/sf_state_pdf_scan/

# Thread-safe lock for writing to COMPLETED_FILE and printing progress.
_lock = threading.Lock()


def load_completed():
    if not COMPLETED_FILE.exists():
        return set()
    with open(COMPLETED_FILE) as f:
        return {line.strip() for line in f if line.strip()}


def mark_completed(spider_name):
    with _lock:
        with open(COMPLETED_FILE, "a") as f:
            f.write(spider_name + "\n")


def _find_scrapy():
    """Return path to the scrapy executable, preferring the project venv."""
    candidates = [
        PROJECT_ROOT / ".venv" / "bin" / "scrapy",          # Mac / Linux venv
        PROJECT_ROOT / ".venv" / "Scripts" / "scrapy.exe",  # Windows venv
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return "scrapy"  # fall back to system PATH


def _run_spider(spider_name, scrapy_cmd):
    """
    Run a single spider as a 'scrapy crawl <name>' subprocess.

    Output is redirected to temp/<spider_name>.log so that parallel spider
    logs don't interleave in the terminal. Progress messages (start / done /
    fail) are printed to stdout with a thread-safe lock.

    Returns (spider_name, returncode).
    """
    log_path = config.TEMP_DIR / f"{spider_name}.log"

    with _lock:
        print(f"[START] {spider_name}")
        print(f"        log → {log_path}")

    with open(log_path, "w") as log_file:
        result = subprocess.run(
            [scrapy_cmd, "crawl", spider_name],
            cwd=str(SPIDER_DIR),
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )

    if result.returncode == 0:
        mark_completed(spider_name)
        with _lock:
            print(f"[DONE]  {spider_name}")
    else:
        with _lock:
            print(f"[FAIL]  {spider_name}  (exit {result.returncode})")
            print(f"        See log for details: {log_path}")

    return spider_name, result.returncode


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Scrapy spiders in parallel (restart-safe)."
    )
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

    # Derive the expected spider name from the domain key.
    domain_spider_filter = None
    if args.domain:
        domain_spider_filter = (
            args.domain.replace(".", "_").replace("-", "_").lower() + "_spider"
        )
        print(f"Domain filter active — looking for spider: {domain_spider_filter}")

    # Discover available spiders via Scrapy's spider loader.
    settings = get_project_settings()
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
        print(f"(Delete {COMPLETED_FILE} or run fresh_start to reset.)")
        sys.exit(0)

    scrapy_cmd = _find_scrapy()
    workers = min(len(to_run), MAX_CONCURRENT_SPIDERS)

    print(f"")
    print(f"Spiders to run : {len(to_run)}")
    print(f"Already done   : {len(completed)}")
    print(f"Parallel workers: {workers}  (MAX_CONCURRENT_SPIDERS={MAX_CONCURRENT_SPIDERS})")
    print(f"Scrapy command : {scrapy_cmd}")
    print(f"Spider logs    : {config.TEMP_DIR}/")
    print(f"")

    failed = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_run_spider, name, scrapy_cmd): name
            for name in to_run
        }
        for future in as_completed(futures):
            name, returncode = future.result()
            if returncode != 0:
                failed.append(name)

    print(f"")
    print(f"Crawl complete.")
    print(f"  Succeeded : {len(to_run) - len(failed)}")
    if failed:
        print(f"  Failed    : {len(failed)}")
        for name in failed:
            print(f"    - {name}  (log: {config.TEMP_DIR}/{name}.log)")
        print(f"  Re-run this script to retry failed spiders (completed ones are skipped).")
    else:
        print(f"  All spiders finished successfully.")
