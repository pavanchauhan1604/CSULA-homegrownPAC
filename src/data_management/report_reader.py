"""Canonical reader for CSULA PDF accessibility Excel reports.

All reporting scripts (historical_analysis, generate_master_report,
generate_master_report_html) import their data-reading logic from here
so that counts, deduplication, and priority classification are identical
across every output.

Key design decisions
--------------------
- Fingerprint-based deduplication: the 'fingerprint' column (SHA-256) is
  the unique key. If the same PDF appears twice in a sheet, the row that
  marks it Low Priority = "No" wins (high-priority takes precedence over
  compliant so we never under-count problems).
- High-priority source of truth: the pre-stamped 'Low Priority' column in
  the Excel file, written by data_export.py using is_high_priority() at
  scan time. No re-evaluation of filters logic at read time — that would
  diverge from the stamped value if thresholds ever change between runs.
- All aggregate metrics (violations, errors/page) are computed over
  deduplicated rows only, so they match the unique-PDF count.
"""

from __future__ import annotations

import io
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import config
import openpyxl

# Matches the timestamp embedded in report filenames:
# e.g.  calstatela-edu_admissions-2026-01-25_06-26-57.xlsx
_TIMESTAMP_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.xlsx$", re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------

def _col_index(header_row: tuple) -> dict[str, int]:
    return {
        str(h).strip(): i
        for i, h in enumerate(header_row)
        if h is not None
    }


def _int_val(raw: Any) -> int:
    try:
        return int(raw) if raw is not None else 0
    except (ValueError, TypeError):
        return 0


def _float_val(raw: Any) -> float:
    try:
        return float(raw) if raw is not None else 0.0
    except (ValueError, TypeError):
        return 0.0


def _parse_timestamp(filename: str) -> datetime | None:
    m = _TIMESTAMP_RE.search(filename)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), config.EXCEL_REPORT_TIMESTAMP_FORMAT)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Core Excel reader — single source of truth for all reporting scripts
# ---------------------------------------------------------------------------

def parse_domain_excel(source: Path | bytes) -> dict | None:
    """Parse one domain Excel report and return a metrics dict.

    *source* can be a file Path or raw bytes (for Teams/Graph downloads).
    Returns None when the file cannot be opened or has no usable data rows.

    Returned dict keys
    ------------------
    unique_pdfs         int   — deduplicated PDF count (by fingerprint)
    high_priority       int   — PDFs where Low Priority == "No" (deduplicated)
    compliant_scanned   int   — unique_pdfs − high_priority
    compliance_pct      float — compliant_scanned / unique_pdfs × 100
    violations_total    int   — sum of violations across unique PDFs
    violations_avg      float — mean violations per unique PDF
    errors_per_page_avg float — mean Errors/Page across unique PDFs
    top_errors          dict  — {error_message: count} top-10 from Failure sheet
    """
    try:
        if isinstance(source, (bytes, bytearray)):
            wb = openpyxl.load_workbook(
                io.BytesIO(source), read_only=True, data_only=True
            )
        else:
            wb = openpyxl.load_workbook(source, read_only=True, data_only=True)
    except Exception as exc:
        print(f"    [WARN] Cannot open workbook: {exc}")
        return None

    try:
        # Prefer "Unique PDFs" sheet; fall back to "Scanned PDFs" for old reports.
        sheet_name = (
            "Unique PDFs" if "Unique PDFs" in wb.sheetnames
            else "Scanned PDFs" if "Scanned PDFs" in wb.sheetnames
            else None
        )
        if sheet_name is None:
            print(f"    [WARN] Neither 'Unique PDFs' nor 'Scanned PDFs' sheet found "
                  f"(sheets: {wb.sheetnames})")
            wb.close()
            return None

        rows = list(wb[sheet_name].iter_rows(values_only=True))
        if len(rows) < 2:
            print(f"    [WARN] '{sheet_name}' sheet has no data rows")
            wb.close()
            return None

        col    = _col_index(rows[0])
        v_idx  = col.get("violations")
        ep_idx = col.get("Errors/Page")
        lp_idx = col.get("Low Priority")
        fp_idx = col.get("fingerprint")

        # ── Fingerprint-deduped accumulation ─────────────────────────────────
        # seen[fingerprint] = {"is_high": bool, "violations": int, "ep": float}
        # When the same fingerprint appears more than once, the high-priority
        # flag wins (is_high=True overrides False) and the last row's numeric
        # values are used.
        seen: dict[str, dict] = {}

        for idx, row in enumerate(rows[1:]):
            if all(c is None for c in row):
                continue

            # Unique key: fingerprint column if present, else positional fallback
            fp_raw = (row[fp_idx] if fp_idx is not None else None)
            key    = str(fp_raw).strip() if fp_raw is not None else ""
            if not key:
                key = f"__row_{idx}"

            raw_lp  = row[lp_idx] if lp_idx is not None else None
            is_high = isinstance(raw_lp, str) and raw_lp.strip().lower() == "no"

            v  = _int_val(row[v_idx]  if v_idx  is not None else None)
            ep = _float_val(row[ep_idx] if ep_idx is not None else None)

            if key not in seen:
                seen[key] = {"is_high": is_high, "v": v, "ep": ep}
            else:
                # Same fingerprint seen before — high-priority flag wins
                if is_high:
                    seen[key]["is_high"] = True
                seen[key]["v"]  = v
                seen[key]["ep"] = ep

        # ── Aggregate metrics over deduplicated rows ──────────────────────────
        unique_pdfs   = len(seen)
        high_priority = sum(1 for r in seen.values() if r["is_high"])
        viol_list     = [r["v"]  for r in seen.values()]
        ep_list       = [r["ep"] for r in seen.values()]

        compliant_scanned = unique_pdfs - high_priority
        compliance_pct    = (
            round(compliant_scanned / unique_pdfs * 100, 1) if unique_pdfs else 0.0
        )
        violations_total  = sum(viol_list)
        violations_avg    = (
            round(violations_total / unique_pdfs, 1) if unique_pdfs else 0.0
        )
        errors_per_page_avg = (
            round(sum(ep_list) / len(ep_list), 2) if ep_list else 0.0
        )

        # ── Top errors from Failure sheet ─────────────────────────────────────
        top_errors: dict[str, int] = {}
        if "Failure" in wb.sheetnames:
            f_rows = list(wb["Failure"].iter_rows(values_only=True))
            if len(f_rows) > 1:
                f_col   = _col_index(f_rows[0])
                msg_idx = f_col.get("error_message")
                if msg_idx is not None:
                    counter: Counter = Counter()
                    for row in f_rows[1:]:
                        if all(c is None for c in row):
                            continue
                        msg = row[msg_idx]
                        if msg:
                            counter[str(msg)[:150]] += 1
                    top_errors = dict(counter.most_common(10))

        return dict(
            unique_pdfs=unique_pdfs,
            high_priority=high_priority,
            compliant_scanned=compliant_scanned,
            compliance_pct=compliance_pct,
            violations_total=violations_total,
            violations_avg=violations_avg,
            errors_per_page_avg=errors_per_page_avg,
            # kept for backwards-compat with historical_analysis rendering
            total_scanned=unique_pdfs,
            top_errors=top_errors,
        )

    except Exception as exc:
        print(f"    [WARN] Error parsing workbook content: {exc}")
        return None
    finally:
        wb.close()


# ---------------------------------------------------------------------------
# Folder / filename helpers
# ---------------------------------------------------------------------------

def find_latest_xlsx(folder: Path) -> Path | None:
    """Return the most recently timestamped .xlsx in *folder*, or None."""
    def _key(p: Path) -> str:
        m = _TIMESTAMP_RE.search(p.name)
        return m.group(1) if m else ""

    candidates = [
        p for p in folder.glob("*.xlsx")
        if not p.name.startswith("~$")
    ]
    return max(candidates, key=_key) if candidates else None


def folder_to_display_name(folder_name: str) -> str:
    """Convert an OneDrive folder name to a human-readable domain string.

    e.g. 'calstatela-edu_admissions' → 'calstatela.edu_admissions'
    Only the portion before the first '_' has dashes converted to dots.
    """
    if "_" in folder_name:
        domain_part, rest = folder_name.split("_", 1)
        return f"{domain_part.replace('-', '.')}_{rest}"
    return folder_name.replace("-", ".")


# ---------------------------------------------------------------------------
# Domain scan collection
# ---------------------------------------------------------------------------

def collect_from_local(
    base_path: Path,
    domains: list[str] | None,
) -> dict[str, list[dict]]:
    """Read all timestamped Excel reports from each domain subfolder.

    Returns ``{display_key: [scan_dict, ...]}`` sorted oldest → newest.

    *domains* — if None, auto-discovers every subfolder that has xlsx files.
    If a list is given, only those domain keys (matching config naming) are
    processed.
    """
    if domains is not None:
        folder_to_domain = {
            config.get_domain_folder_name(d).lower(): config.get_domain_folder_name(d)
            for d in domains
        }
    else:
        folder_to_domain = None

    data: dict[str, list[dict]] = {}

    for entry in sorted(base_path.iterdir()):
        if not entry.is_dir():
            continue

        if folder_to_domain is not None:
            if entry.name.lower() not in folder_to_domain:
                continue
            display_key = folder_to_domain[entry.name.lower()]
        else:
            display_key = entry.name

        scans: list[dict] = []
        for xlsx in sorted(entry.glob("*.xlsx")):
            if xlsx.name.startswith("~$"):
                continue
            ts = _parse_timestamp(xlsx.name)
            if ts is None:
                print(f"    [SKIP] {xlsx.name} — filename does not match timestamp pattern")
                continue
            print(f"    [READ] {xlsx.name}")
            metrics = parse_domain_excel(xlsx)
            if metrics:
                metrics["timestamp"] = ts
                metrics["filename"]  = xlsx.name
                metrics["rel_path"]  = str(xlsx.relative_to(base_path))
                scans.append(metrics)
            else:
                print(f"    [SKIP] {xlsx.name} — could not extract metrics")

        if scans:
            scans.sort(key=lambda s: s["timestamp"])
            data[display_key] = scans

    return data
