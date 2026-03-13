"""Generate a master Excel report summarising all domains synced to OneDrive.

For every domain folder found in TEAMS_ONEDRIVE_PATH this script:
  1. Finds the latest .xlsx report inside that folder
  2. Reads the 'Unique PDFs' sheet
  3. Counts total unique PDFs and high-priority PDFs
  4. Writes / overwrites  TEAMS_ONEDRIVE_PATH/Master Report.xlsx

Usage
-----
    python scripts/generate_master_report.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

import config
from src.core.filters import get_priority_level
from scripts.sharepoint_sync import row_to_priority_data, read_unique_pdfs_sheet

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TS_RE = re.compile(r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.xlsx$", re.IGNORECASE)


def find_latest_xlsx(folder: Path) -> Path | None:
    """Return the most recent .xlsx in *folder* by filename timestamp."""
    def _key(p: Path):
        m = _TS_RE.search(p.name)
        return m.group(1) if m else ""
    candidates = [p for p in folder.glob("*.xlsx") if not p.name.startswith("~$")]
    return max(candidates, key=_key) if candidates else None


def folder_to_display_name(folder_name: str) -> str:
    """Convert folder name back to a readable domain string.

    e.g. 'www-calstatela-edu_admissions' -> 'www.calstatela.edu_admissions'
    Only the portion before the first '_' has dashes converted back to dots.
    """
    if "_" in folder_name:
        domain_part, rest = folder_name.split("_", 1)
        return f"{domain_part.replace('-', '.')}_{rest}"
    return folder_name.replace("-", ".")


def count_pdfs(pdf_rows: list) -> tuple[int, int]:
    """Return (total_unique, high_priority_count) from Unique PDFs sheet rows.

    pdf_uri cells are stored as =HYPERLINK(...) formulas in the Excel.  When the
    file has never been opened in Microsoft Excel the cached value is None and
    data_only=True returns None for those cells.  Use 'fingerprint' (a plain-text
    column) as the dedup key so counts are always correct.
    """
    priority_order = {"high": 0, "medium": 1, "low": 2}

    # Deduplicate by fingerprint (plain text, never a formula).
    # Fall back to row index so every row still counts even if fingerprint is absent.
    unique: dict[str, dict] = {}
    for idx, row in enumerate(pdf_rows):
        key = str(row.get("fingerprint") or "").strip() or f"__row_{idx}"
        try:
            pdata = row_to_priority_data(row)
            level, _, _ = get_priority_level(pdata)
        except Exception:
            level = "low"

        existing = unique.get(key)
        if existing is None or priority_order[level] < priority_order[existing["level"]]:
            unique[key] = {"level": level}

    total = len(unique)
    high = sum(1 for v in unique.values() if v["level"] == "high")
    return total, high


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    onedrive_path = Path(config.TEAMS_ONEDRIVE_PATH)
    if not onedrive_path.exists():
        print(f"[ERROR] OneDrive folder not found: {onedrive_path}")
        sys.exit(1)

    output_path = onedrive_path / "Master Report.xlsx"

    rows: list[tuple[str, int, int]] = []  # (domain_display, total_unique, high_count)

    for folder in sorted(onedrive_path.iterdir()):
        if not folder.is_dir():
            continue
        # Skip special / meta folders
        if folder.name.startswith(".") or folder.name in {"Mail Drafts"}:
            continue

        xlsx = find_latest_xlsx(folder)
        if not xlsx:
            print(f"  [SKIP] No Excel found in: {folder.name}")
            continue

        try:
            pdf_rows = read_unique_pdfs_sheet(xlsx)
        except Exception as e:
            print(f"  [SKIP] Could not read {xlsx.name}: {e}")
            continue

        total, high = count_pdfs(pdf_rows)
        display = folder_to_display_name(folder.name)
        rows.append((display, total, high))
        print(f"  [OK] {display}: {total} unique PDFs, {high} high priority")

    # Build workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Master Report"

    header_fill = PatternFill("solid", fgColor="003262")
    header_font = Font(bold=True, color="FFFFFF")
    headers = ["Domain", "Total Unique PDFs", "High Priority PDFs"]

    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for row_idx, (domain, total, high) in enumerate(rows, start=2):
        ws.cell(row=row_idx, column=1, value=domain)
        ws.cell(row=row_idx, column=2, value=total).alignment = Alignment(horizontal="center")
        ws.cell(row=row_idx, column=3, value=high).alignment = Alignment(horizontal="center")

    # Auto-fit column widths
    ws.column_dimensions["A"].width = 50
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 22

    wb.save(output_path)
    print(f"\n[DONE] Master Report saved → {output_path}")
    print(f"       {len(rows)} domains | {sum(r[1] for r in rows)} total unique PDFs | {sum(r[2] for r in rows)} high priority")


if __name__ == "__main__":
    main()
