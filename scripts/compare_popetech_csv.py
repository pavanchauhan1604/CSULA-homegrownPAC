#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


HREF_RE = re.compile(r"href\s*=\s*\"([^\"]+)\"", re.IGNORECASE)


def norm_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    # Strip fragments; keep query
    return url.split("#", 1)[0]


def extract_href_from_html(html: str) -> str:
    html = html or ""
    match = HREF_RE.search(html)
    if not match:
        return ""
    return norm_url(match.group(1))


def load_popetech_hrefs(csv_path: Path) -> tuple[list[str], list[str]]:
    hrefs: list[str] = []
    page_urls: list[str] = []

    with csv_path.open(newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # PopeTech exports vary: some use 'url', others use 'uri'
            page_urls.append(norm_url(row.get("url") or row.get("uri") or ""))
            href = extract_href_from_html(row.get("html", ""))
            if href:
                hrefs.append(href)

    return hrefs, page_urls


def load_scanned_urls(scanned_pdfs_path: Path) -> set[str]:
    urls: set[str] = set()
    if not scanned_pdfs_path.exists():
        return urls

    with scanned_pdfs_path.open(encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.strip().split(" ")
            if parts:
                urls.add(norm_url(parts[0]))

    return urls


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Popetech link export vs our scanned_pdfs.txt")
    parser.add_argument("--popetech-csv", required=True, help="Path to Popetech CSV export")
    parser.add_argument(
        "--scanned-pdfs",
        default=str(Path("output/scans/asicalstatela-org/scanned_pdfs.txt")),
        help="Path to scanned_pdfs.txt from our crawler",
    )
    args = parser.parse_args()

    pop_path = Path(args.popetech_csv)
    scan_path = Path(args.scanned_pdfs)

    hrefs, page_urls = load_popetech_hrefs(pop_path)

    href_set = set(hrefs)
    page_set = set(u for u in page_urls if u)

    print("Popetech CSV:", pop_path)
    print("- Rows (page->link):", len(page_urls))
    print("- Unique page URLs:", len(page_set))
    print("- Extracted hrefs:", len(hrefs))
    print("- Unique hrefs:", len(href_set))

    # Classify hrefs
    ext_counter: Counter[str] = Counter()
    same_domain = 0
    other_domain = 0
    non_http = 0
    with_query = 0
    pdf_suffix = 0

    for u in href_set:
        if not (u.startswith("http://") or u.startswith("https://")):
            non_http += 1
            continue

        parsed = urlparse(u)
        host = (parsed.netloc or "").lower()
        path = parsed.path or ""

        if parsed.query:
            with_query += 1

        filename = path.rsplit("/", 1)[-1]
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        ext_counter[ext] += 1

        if path.lower().endswith(".pdf"):
            pdf_suffix += 1

        if host.endswith("asicalstatela.org"):
            same_domain += 1
        else:
            other_domain += 1

    print("\nUnique hrefs breakdown:")
    print("- http(s) same-domain:", same_domain)
    print("- http(s) other-domain:", other_domain)
    print("- non-http(s):", non_http)
    print("- with querystring:", with_query)
    print("- end with .pdf:", pdf_suffix)
    print("- top extensions:", ext_counter.most_common(12))

    scanned = load_scanned_urls(scan_path)
    pop_pdfs = {u for u in href_set if (u.startswith(("http://", "https://")) and urlparse(u).path.lower().endswith(".pdf"))}

    missing = sorted(pop_pdfs - scanned)
    extra = sorted(scanned - pop_pdfs)

    print("\nOur crawler output:", scan_path)
    print("- Unique URLs in scanned_pdfs.txt:", len(scanned))
    print("\nPopetech vs our crawler (.pdf URLs only):")
    print("- Popetech unique .pdf URLs:", len(pop_pdfs))
    print("- Popetech .pdf URLs missing from our scan:", len(missing))
    print("- Our scanned URLs not present in Popetech .pdf set:", len(extra))

    if missing:
        print("\nSample missing (first 25):")
        for u in missing[:25]:
            print(" ", u)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
