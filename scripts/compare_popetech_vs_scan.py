import argparse
import csv
from urllib.parse import urlsplit, urlunsplit

BASE_DEFAULT = "https://www.calstatela.edu"


def norm_url(url: str, *, base: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""

    if url.startswith("//"):
        url = "https:" + url
    if url.startswith("/"):
        url = base.rstrip("/") + url

    parts = urlsplit(url)

    scheme = (parts.scheme or "").lower()
    hostname = (parts.hostname or "").lower() if parts.hostname else ""

    # Canonicalize scheme for the target site to avoid false diffs.
    # Popetech exports mostly https; our crawl may encounter http links.
    if hostname.endswith("asicalstatela.org") and scheme in {"http", "https", ""}:
        scheme = "https"

    if hostname:
        netloc = hostname
        if parts.port:
            netloc = f"{hostname}:{parts.port}"
        parts = parts._replace(scheme=scheme, netloc=netloc)
    else:
        parts = parts._replace(scheme=scheme)

    parts = parts._replace(fragment="")
    return urlunsplit(parts)


def host_suffix_match(url: str, *, host_suffix: str) -> bool:
    if not host_suffix:
        return True
    host_suffix = host_suffix.lower().lstrip(".")
    try:
        hostname = (urlsplit(url).hostname or "").lower()
    except Exception:
        return False
    return hostname == host_suffix or hostname.endswith("." + host_suffix)


def read_popetech_csv(csv_path: str, *, base: str):
    rows = 0
    page_urls: set[str] = set()
    pdf_urls: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    pdf_to_pages: dict[str, set[str]] = {}
    relative_pdf_urls = 0

    with open(csv_path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows += 1
            # Popetech exports vary by version:
            # - Some use 'url' for the page URL
            # - Some use 'uri' for the page URL
            page_raw = r.get("url") or r.get("uri") or ""
            pdf_raw = r.get("text", "")

            if (pdf_raw or "").strip().startswith("/"):
                relative_pdf_urls += 1

            page = norm_url(page_raw, base=base)
            pdf = norm_url(pdf_raw, base=base)

            if page:
                page_urls.add(page)
            if pdf:
                pdf_urls.add(pdf)
            if page and pdf:
                pairs.add((pdf, page))
                pdf_to_pages.setdefault(pdf, set()).add(page)

    return {
        "rows": rows,
        "unique_pages": page_urls,
        "unique_pdfs": pdf_urls,
        "unique_pairs": pairs,
        "pdf_to_pages": pdf_to_pages,
        "relative_pdf_urls": relative_pdf_urls,
    }


def read_scan_txt(scan_path: str, *, base: str):
    pdf_urls: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    parent_pages: set[str] = set()

    with open(scan_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split(None, 1)
            pdf = norm_url(parts[0], base=base)
            parent = norm_url(parts[1] if len(parts) > 1 else "", base=base)

            if pdf:
                pdf_urls.add(pdf)
            if pdf and parent:
                pairs.add((pdf, parent))
                parent_pages.add(parent)

    return {
        "unique_pdfs": pdf_urls,
        "unique_pairs": pairs,
        "parent_pages": parent_pages,
    }


def read_visited_pages_txt(visited_path: str, *, base: str) -> set[str]:
    visited: set[str] = set()
    with open(visited_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            u = norm_url(line.strip(), base=base)
            if u:
                visited.add(u)
    return visited


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare Popetech export (link->pdf CSV) vs our scanned_pdfs.txt output"
    )
    parser.add_argument(
        "--pop",
        required=True,
        help="Path to Popetech CSV (typically: title,uri/text/html or title,url/text/html)",
    )
    parser.add_argument("--scan", required=True, help="Path to scanned_pdfs.txt")
    parser.add_argument(
        "--base",
        default=BASE_DEFAULT,
        help=f"Base URL for relative PDFs (default: {BASE_DEFAULT})",
    )
    parser.add_argument(
        "--host-suffix",
        default="",
        help="If set, only compare PDFs whose hostname matches this suffix (e.g. asicalstatela.org)",
    )
    parser.add_argument(
        "--visited",
        default="",
        help="Optional path to visited_pages.txt (enables traversal vs extraction diagnostics)",
    )
    parser.add_argument("--sample", type=int, default=20, help="How many sample URLs to print")
    args = parser.parse_args()

    pop = read_popetech_csv(args.pop, base=args.base)
    scan = read_scan_txt(args.scan, base=args.base)

    pop_pages: set[str] = pop["unique_pages"]
    pop_pdfs = pop["unique_pdfs"]
    scan_pdfs = scan["unique_pdfs"]

    pop_pdf_to_pages: dict[str, set[str]] = pop.get("pdf_to_pages", {})
    scan_parent_pages: set[str] = scan.get("parent_pages", set())

    visited_pages: set[str] = set()
    if args.visited:
        visited_pages = read_visited_pages_txt(args.visited, base=args.base)

    if args.host_suffix:
        pop_pages = {u for u in pop_pages if host_suffix_match(u, host_suffix=args.host_suffix)}
        pop_pdfs = {u for u in pop_pdfs if host_suffix_match(u, host_suffix=args.host_suffix)}
        scan_pdfs = {u for u in scan_pdfs if host_suffix_match(u, host_suffix=args.host_suffix)}
        pop_pdf_to_pages = {
            pdf: {p for p in pages if host_suffix_match(p, host_suffix=args.host_suffix)}
            for pdf, pages in pop_pdf_to_pages.items()
            if host_suffix_match(pdf, host_suffix=args.host_suffix)
        }
        if visited_pages:
            visited_pages = {
                u for u in visited_pages if host_suffix_match(u, host_suffix=args.host_suffix)
            }

    common = pop_pdfs & scan_pdfs
    pop_only = pop_pdfs - scan_pdfs
    scan_only = scan_pdfs - pop_pdfs

    # Heuristic: if we have seen a Popetech page as a parent page in our output,
    # but still missed its PDF, this suggests extraction gaps more than traversal gaps.
    pop_only_with_seen_parent = 0
    for pdf in pop_only:
        pages = pop_pdf_to_pages.get(pdf) or set()
        if pages and any(p in scan_parent_pages for p in pages):
            pop_only_with_seen_parent += 1

    pop_only_with_visited_page = 0
    pop_only_with_visited_page_urls: list[str] = []
    if visited_pages:
        for pdf in pop_only:
            pages = pop_pdf_to_pages.get(pdf) or set()
            if pages and any(p in visited_pages for p in pages):
                pop_only_with_visited_page += 1
                pop_only_with_visited_page_urls.append(pdf)

    pop_pages_visited = 0
    pop_pages_not_visited: list[str] = []
    if visited_pages:
        pop_pages_visited = len({p for p in pop_pages if p in visited_pages})
        pop_pages_not_visited = sorted({p for p in pop_pages if p not in visited_pages})

    print("POPETECH")
    print(f"  rows: {pop['rows']}")
    print(f"  unique_pages: {len(pop_pages)}")
    if visited_pages:
        print(f"  unique_pages_visited_by_our_crawl: {pop_pages_visited}")
    print(f"  unique_pdfs: {len(pop_pdfs)}")
    print(f"  unique_pairs: {len(pop['unique_pairs'])}")
    print(f"  relative_pdf_urls: {pop['relative_pdf_urls']}")
    print()

    print("OUR CRAWL")
    print(f"  unique_pdfs: {len(scan_pdfs)}")
    print(f"  unique_pairs: {len(scan['unique_pairs'])}")
    print()

    if args.host_suffix:
        print(f"FILTER")
        print(f"  host_suffix: {args.host_suffix}")
        print()

    print("OVERLAP")
    print(f"  common_unique_pdfs: {len(common)}")
    print(f"  popetech_unique_pdfs_missing_in_our_crawl: {len(pop_only)}")
    if pop_only:
        print(
            f"  pop_only_with_parent_page_seen_in_our_output: {pop_only_with_seen_parent}"
        )
        if visited_pages:
            print(
                f"  pop_only_with_page_visited_by_our_crawl: {pop_only_with_visited_page}"
            )
    print(f"  our_unique_pdfs_missing_in_popetech: {len(scan_only)}")

    if args.sample > 0:
        print("\nSAMPLES")
        print(f"  pop_only (first {args.sample}):")
        for i, u in enumerate(sorted(pop_only)[: args.sample], 1):
            print(f"    {i:>2}. {u}")

        if visited_pages:
            print(f"  pop_only_with_page_visited_by_our_crawl (first {args.sample}):")
            for i, u in enumerate(sorted(pop_only_with_visited_page_urls)[: args.sample], 1):
                print(f"    {i:>2}. {u}")
            print(f"  pop_pages_not_visited_by_our_crawl (first {args.sample}):")
            for i, u in enumerate(pop_pages_not_visited[: args.sample], 1):
                print(f"    {i:>2}. {u}")

        print(f"  scan_only (first {args.sample}):")
        for i, u in enumerate(sorted(scan_only)[: args.sample], 1):
            print(f"    {i:>2}. {u}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
