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
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles import Font, PatternFill, Alignment

import config
from src.core.filters import get_priority_level
from scripts.sharepoint_sync import row_to_priority_data, read_unique_pdfs_sheet

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TS_RE = re.compile(r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.xlsx$", re.IGNORECASE)

SHEET_DATA = "Data"
SHEET_DASHBOARD = "Dashboard"
SHEET_RUN_INDEX = "Run Index"

HEADER_FILL = PatternFill("solid", fgColor="003262")
HEADER_FONT = Font(bold=True, color="FFFFFF")


def _style_header_row(ws, headers: list[str], row: int = 1) -> None:
    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")


def _ensure_workbook(path: Path) -> openpyxl.Workbook:
    wb = openpyxl.load_workbook(path) if path.exists() else openpyxl.Workbook()
    if "Sheet" in wb.sheetnames and len(wb.sheetnames) == 1:
        del wb["Sheet"]
    return wb


def _ensure_data_sheet(wb: openpyxl.Workbook):
    ws = wb[SHEET_DATA] if SHEET_DATA in wb.sheetnames else wb.create_sheet(SHEET_DATA, 0)
    _style_header_row(ws, ["Run Timestamp", "Domain", "Total Unique PDFs", "High Priority PDFs"])
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 22
    ws.column_dimensions["D"].width = 22
    ws.freeze_panes = "A2"
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


def _refresh_dashboard(wb: openpyxl.Workbook, run_values: list[str]):
    ws = wb[SHEET_DASHBOARD] if SHEET_DASHBOARD in wb.sheetnames else wb.create_sheet(SHEET_DASHBOARD)

    if ws.max_row > 1:
        ws.delete_rows(1, ws.max_row)
    if ws.max_column > 1:
        ws.delete_cols(1, ws.max_column)

    ws["A1"] = "Master Report Dashboard"
    ws["A1"].font = Font(bold=True, size=14)

    ws["A3"] = "Select Run Timestamp"
    ws["A3"].font = Font(bold=True)
    ws["B3"] = run_values[0] if run_values else ""

    list_end = max(1, len(run_values))
    dv = DataValidation(type="list", formula1=f"='{SHEET_RUN_INDEX}'!$A$1:$A${list_end}", allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(ws["B3"])

    ws["A5"] = "Total Unique PDFs"
    ws["B5"] = f'=SUMIFS({SHEET_DATA}!$C:$C,{SHEET_DATA}!$A:$A,$B$3)'
    ws["A6"] = "High Priority PDFs"
    ws["B6"] = f'=SUMIFS({SHEET_DATA}!$D:$D,{SHEET_DATA}!$A:$A,$B$3)'

    _style_header_row(ws, ["Domain", "Total Unique PDFs", "High Priority PDFs"], row=9)
    ws["A10"] = f'=IFERROR(FILTER({SHEET_DATA}!$B:$D,{SHEET_DATA}!$A:$A=$B$3),"No data for selected run")'

    ws.column_dimensions["A"].width = 50
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 22
    ws.freeze_panes = "A10"


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

    # Sort by high priority PDFs descending
    rows.sort(key=lambda x: x[2], reverse=True)

    run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    wb = _ensure_workbook(output_path)
    data_ws = _ensure_data_sheet(wb)
    run_index_ws = _ensure_run_index_sheet(wb)

    for domain, total, high in rows:
        data_ws.append([run_ts, domain, total, high])
        data_ws.cell(row=data_ws.max_row, column=3).alignment = Alignment(horizontal="center")
        data_ws.cell(row=data_ws.max_row, column=4).alignment = Alignment(horizontal="center")

    run_values = _refresh_run_index(run_index_ws, data_ws)
    _refresh_dashboard(wb, run_values)

    wb.save(output_path)
    print(f"\n[DONE] Master Report saved → {output_path}")
    print(f"       run timestamp: {run_ts}")
    print(f"       {len(rows)} domains | {sum(r[1] for r in rows)} total unique PDFs | {sum(r[2] for r in rows)} high priority")
    print(f"       {len(run_values)} runs available in Dashboard dropdown")


if __name__ == "__main__":
    main()
