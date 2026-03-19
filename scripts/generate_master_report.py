"""Generate a historical master Excel report summarising all synced domains.

For every domain folder found in TEAMS_ONEDRIVE_PATH this script:
    1. Finds the latest .xlsx report inside that folder
    2. Reads the 'Unique PDFs' sheet
    3. Counts total unique PDFs and high-priority PDFs
    4. Appends one run snapshot to a historical Data sheet
    5. Refreshes a Dashboard sheet with a run-date dropdown selector

Usage
-----
        python scripts/generate_master_report.py
"""

from __future__ import annotations

import re
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles import Font, PatternFill, Alignment

import config
from scripts.sharepoint_sync import read_unique_pdfs_sheet

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TS_RE = re.compile(r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.xlsx$", re.IGNORECASE)

SHEET_DATA = "Data"
SHEET_DASHBOARD = "Dashboard"
SHEET_RUN_INDEX = "Run Index"

HEADER_FILL = PatternFill("solid", fgColor="003262")
HEADER_FONT = Font(bold=True, color="FFFFFF")
LOCK_RETRY_ATTEMPTS = 3
LOCK_RETRY_DELAY_SECONDS = 2


def _style_header_row(ws, headers: list[str], row: int = 1) -> None:
    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")


def _ensure_workbook(path: Path) -> openpyxl.Workbook:
    if not path.exists():
        wb = openpyxl.Workbook()
    else:
        last_error: Exception | None = None
        wb = None
        for attempt in range(1, LOCK_RETRY_ATTEMPTS + 1):
            try:
                wb = openpyxl.load_workbook(path)
                break
            except PermissionError as e:
                last_error = e
                if attempt < LOCK_RETRY_ATTEMPTS:
                    time.sleep(LOCK_RETRY_DELAY_SECONDS)
        if wb is None:
            raise RuntimeError(
                f"Cannot open '{path}'. The file appears to be locked. "
                "Close Master/Master Report.xlsx in Excel (and let OneDrive finish syncing)"
                "then run this script again."
            ) from last_error

    if "Sheet" in wb.sheetnames and len(wb.sheetnames) == 1:
        del wb["Sheet"]
    return wb


def _ensure_data_sheet(wb: openpyxl.Workbook):
    ws = wb[SHEET_DATA] if SHEET_DATA in wb.sheetnames else wb.create_sheet(SHEET_DATA, 0)
    _style_header_row(ws, ["Scan Date", "Domain", "Total Unique PDFs", "High Priority PDFs"])
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 22
    ws.column_dimensions["D"].width = 22
    ws.freeze_panes = "A2"
    
    # Add auto-filter arrows to the header row
    ws.auto_filter.ref = "A1:D1"
    
    return ws


def _ensure_run_index_sheet(wb: openpyxl.Workbook):
    ws = wb[SHEET_RUN_INDEX] if SHEET_RUN_INDEX in wb.sheetnames else wb.create_sheet(SHEET_RUN_INDEX)
    ws.sheet_state = "hidden"
    return ws


def _refresh_run_index(run_index_ws, data_ws) -> list[str]:
    run_values = {
        str(data_ws.cell(row=row, column=1).value).strip()
        for row in range(2, data_ws.max_row + 1)
        if data_ws.cell(row=row, column=1).value
    }
    ordered = sorted(run_values, reverse=True)

    run_index_ws.delete_rows(1, run_index_ws.max_row)
    for i, val in enumerate(ordered, start=1):
        run_index_ws.cell(row=i, column=1, value=val)
    run_index_ws.sheet_state = "hidden"
    return ordered


def _refresh_dashboard(wb: openpyxl.Workbook, run_values: list[str], current_rows: list[tuple[str, str, int, int]]):
    ws = wb[SHEET_DASHBOARD] if SHEET_DASHBOARD in wb.sheetnames else wb.create_sheet(SHEET_DASHBOARD)

    # Clear all existing content
    for row in ws.iter_rows():
        for cell in row:
            cell.value = None

    ws["A1"] = "Master Report Dashboard"
    ws["A1"].font = Font(bold=True, size=14)

    ws["A3"] = "Latest Scan Date"
    ws["A3"].font = Font(bold=True)
    ws["B3"] = run_values[0] if run_values else ""

    # Dropdown for reference – shows all available scan dates in the hidden Run Index sheet.
    # NOTE: The domain table below always reflects the most recent roll-up (written as static values).
    # To view older runs, filter the Data sheet by Scan Date.
    list_end = max(1, len(run_values))
    dv = DataValidation(type="list", formula1=f"='{SHEET_RUN_INDEX}'!$A$1:$A${list_end}", allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(ws["B3"])

    ws["A5"] = "Total Unique PDFs (latest roll-up)"
    ws["B5"] = sum(r[2] for r in current_rows)
    ws["B5"].alignment = Alignment(horizontal="center")
    ws["A6"] = "High Priority PDFs (latest roll-up)"
    ws["B6"] = sum(r[3] for r in current_rows)
    ws["B6"].alignment = Alignment(horizontal="center")

    ws["A8"] = "Tip: For older runs, go to the Data sheet and use Excel's column filter on 'Scan Date'."
    ws["A8"].font = Font(italic=True, color="666666")

    _style_header_row(ws, ["Domain", "Total Unique PDFs", "High Priority PDFs"], row=10)

    for i, (_, domain, total, high) in enumerate(current_rows, start=11):
        ws.cell(row=i, column=1, value=domain)
        ws.cell(row=i, column=2, value=total).alignment = Alignment(horizontal="center")
        ws.cell(row=i, column=3, value=high).alignment = Alignment(horizontal="center")

    ws.column_dimensions["A"].width = 50
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 22
    ws.freeze_panes = "A11"


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

    High priority is defined as Low Priority == "No" — matching the definition
    used by historical_analysis.py and the compliance % calculation so that all
    reports are consistent. A PDF stays high priority until a content manager
    explicitly marks it "Yes" (safe/done) in the Low Priority column.

    pdf_uri cells are stored as =HYPERLINK(...) formulas in the Excel. Use
    'fingerprint' (a plain-text column) as the dedup key so counts are correct
    even when the file has never been opened in Excel (cached formula values = None).
    """
    seen: dict[str, bool] = {}  # fingerprint → is_high_priority
    for idx, row in enumerate(pdf_rows):
        key = str(row.get("fingerprint") or "").strip() or f"__row_{idx}"
        raw_lp = row.get("Low Priority") or ""
        is_high = isinstance(raw_lp, str) and raw_lp.strip().lower() == "no"
        # If same fingerprint appears twice, mark high if either row is high
        if key not in seen or is_high:
            seen[key] = is_high

    total = len(seen)
    high = sum(1 for v in seen.values() if v)
    return total, high


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    onedrive_path = Path(config.TEAMS_ONEDRIVE_PATH)
    if not onedrive_path.exists():
        print(f"[ERROR] OneDrive folder not found: {onedrive_path}")
        sys.exit(1)

    master_dir = onedrive_path / "Master"
    master_dir.mkdir(exist_ok=True)
    output_path = master_dir / "Master Report.xlsx"

    rows: list[tuple[str, str, int, int]] = []  # (scan_date, domain_display, total_unique, high_count)

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
        
        # Extract the logical scan date (YYYY-MM-DD) from the xlsx filename so that
        # the dashboard reflects the actual time the domain was scanned, rather than
        # the time this master script ran.
        m = _TS_RE.search(xlsx.name)
        scan_date = m.group(1)[:10] if m else datetime.today().strftime("%Y-%m-%d")
        
        rows.append((scan_date, display, total, high))
        print(f"  [OK] {display}: {total} unique PDFs, {high} high priority (scan: {scan_date})")

    # Sort by high priority PDFs descending
    rows.sort(key=lambda x: x[3], reverse=True)

    wb = _ensure_workbook(output_path)
    data_ws = _ensure_data_sheet(wb)
    run_index_ws = _ensure_run_index_sheet(wb)

    for scan_date, domain, total, high in rows:
        data_ws.append([scan_date, domain, total, high])
        data_ws.cell(row=data_ws.max_row, column=3).alignment = Alignment(horizontal="center")
        data_ws.cell(row=data_ws.max_row, column=4).alignment = Alignment(horizontal="center")

    run_values = _refresh_run_index(run_index_ws, data_ws)
    _refresh_dashboard(wb, run_values, rows)

    try:
        wb.save(output_path)
    except PermissionError as e:
        raise RuntimeError(
            f"Cannot save '{output_path}'. The file appears to be locked. "
            "Close Master/Master Report.xlsx in Excel (and let OneDrive finish syncing)"
            "then run this script again."
        ) from e

    print(f"\n[DONE] Master Report saved → {output_path}")
    print(f"       {len(rows)} domains | {sum(r[2] for r in rows)} total unique PDFs | {sum(r[3] for r in rows)} high priority")
    print(f"       {len(run_values)} scan dates available in Dashboard dropdown")


if __name__ == "__main__":
    main()
