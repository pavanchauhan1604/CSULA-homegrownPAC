import argparse
import csv
import pathlib
import sys
from urllib.parse import urljoin, urlsplit, urlunsplit

import openpyxl

# Ensure repo root is on sys.path so `import config` works when run from scripts/.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import config  # noqa: E402


def normalize_url(url: str) -> str:
    url = url.strip()
    parts = urlsplit(url)
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    # Normalize common www.
    if netloc.startswith("www."):
        netloc = netloc[4:]
    # Drop fragment
    return urlunsplit((scheme, netloc, parts.path, parts.query, ""))


def extract_url_from_hyperlink_formula(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and value.startswith("=HYPERLINK("):
        # Typical form: =HYPERLINK("url","label")
        parts = value.split('"')
        if len(parts) >= 2:
            return parts[1]
    if isinstance(value, str):
        return value
    return None


def load_xlsx_unique_pdfs(site: str) -> tuple[pathlib.Path, set[str]]:
    xlsx_path = pathlib.Path(config.get_excel_report_path(site, prefer_latest=True))
    wb = openpyxl.load_workbook(xlsx_path, data_only=False, read_only=True)
    ws = wb["Unique PDFs"]

    urls: set[str] = set()
    # Column A is PDF Title; column B is the PDF URL
    for (v,) in ws.iter_rows(min_row=2, min_col=2, max_col=2, values_only=True):
        raw = extract_url_from_hyperlink_formula(v)
        if raw:
            urls.add(normalize_url(raw))

    return xlsx_path, urls


def load_popetech_unique_pdfs(csv_path: pathlib.Path, base_url: str) -> set[str]:
    unique: set[str] = set()
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pdf = (row.get("text") or "").strip()
            if not pdf:
                continue
            absolute = urljoin(base_url, pdf)
            unique.add(normalize_url(absolute))
    return unique


def infer_base_url_from_popetech_csv(csv_path: pathlib.Path) -> str | None:
    """Infer base URL from the CSV's page URL column (`uri`), if present."""
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                page_url = (row.get("uri") or "").strip()
                if not page_url:
                    continue
                parts = urlsplit(page_url)
                if parts.scheme and parts.netloc:
                    return f"{parts.scheme}://{parts.netloc}"
    except Exception:
        return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare PopeTech alerts_link_to_pdf_document.csv to latest XLSX Unique PDFs sheet."
    )
    parser.add_argument("--site", required=True)
    parser.add_argument("--popetech-csv", required=True)
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL for joining relative PDF paths from PopeTech CSV (auto-inferred from CSV if omitted)",
    )
    args = parser.parse_args()

    pop_path = pathlib.Path(args.popetech_csv)

    base_url = args.base_url or infer_base_url_from_popetech_csv(pop_path) or "https://www.calstatela.edu"

    xlsx_path, xlsx_unique = load_xlsx_unique_pdfs(args.site)
    pop_unique = load_popetech_unique_pdfs(pop_path, base_url)

    common = pop_unique & xlsx_unique
    missing = pop_unique - xlsx_unique
    extra = xlsx_unique - pop_unique

    print("site:", args.site)
    print("xlsx_path:", xlsx_path)
    print("popetech_csv:", pop_path)
    print("base_url:", base_url)
    print("popetech_unique_pdfs:", len(pop_unique))
    print("xlsx_unique_pdfs:", len(xlsx_unique))
    print("common_unique_pdfs:", len(common))
    print("missing_in_xlsx:", len(missing))
    print("extra_in_xlsx:", len(extra))

    if missing:
        print("\nMissing PDFs (in PopeTech, not in XLSX):")
        for u in sorted(missing):
            print(" -", u)

    if extra:
        print("\nExtra PDFs (in XLSX, not in PopeTech):")
        for u in sorted(extra):
            print(" -", u)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
