"""Diagnostic: analyse PDF accessibility data to calibrate is_high_priority() thresholds.

Reads every domain's latest Excel report (Unique PDFs sheet) from OneDrive and
prints a breakdown of the current data to help decide the right violation thresholds.

Usage
-----
    python scripts/diagnose_priority_thresholds.py
    python scripts/diagnose_priority_thresholds.py --source local --local-path "C:\\path\\to\\folder"
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import config
from scripts.sharepoint_sync import read_unique_pdfs_sheet
from src.data_management.report_reader import _coerce_int, _coerce_bool, find_latest_xlsx as _find_latest_xlsx


def collect_rows(source_path: Path) -> list[dict]:
    """Collect all PDF rows from latest Excel in every domain subfolder."""
    all_rows = []
    for folder in sorted(source_path.iterdir()):
        if not folder.is_dir() or folder.name.startswith(".") or folder.name in {"Master", "Mail Drafts"}:
            continue
        xlsx = _find_latest_xlsx(folder)
        if not xlsx:
            continue
        try:
            rows = read_unique_pdfs_sheet(xlsx)
            all_rows.extend(rows)
            print(f"  [OK] {folder.name}: {len(rows)} rows")
        except Exception as e:
            print(f"  [SKIP] {folder.name}: {e}")
    return all_rows


def analyse(rows: list[dict]) -> None:
    total = len(rows)
    if total == 0:
        print("No rows found.")
        return

    # ── Per-row metrics ────────────────────────────────────────────────────
    errors_per_page   = []
    tagged_vals       = []
    text_types        = []
    has_form_vals     = []
    approved_vals     = []

    for row in rows:
        page_count    = _coerce_int(row.get("page_count", 0))
        # failed_checks is stored as Yes/No in Excel — use Errors/Page directly
        ep_raw        = row.get("Errors/Page", 0)
        ep            = _coerce_int(ep_raw) if str(ep_raw).strip().lower() not in ("yes", "no", "") else 0
        errors_per_page.append(ep)
        tagged_vals.append(1 if _coerce_bool(row.get("tagged")) else 0)
        text_types.append(str(row.get("pdf_text_type") or "").strip())
        has_form_vals.append(1 if _coerce_bool(row.get("has_form")) else 0)
        approved_vals.append(1 if _coerce_bool(row.get("approved_pdf_exporter")) else 0)

    approved_count = sum(approved_vals)

    print(f"\n{'='*60}")
    print(f"TOTAL UNIQUE PDFs: {total}")
    print(f"{'='*60}")

    # ── Critical structural failures (non-negotiable high priority) ────────
    untagged      = sum(1 for t in tagged_vals if t == 0)
    image_only    = sum(1 for t in text_types if t == "Image Only")
    no_content    = sum(1 for t in text_types if t == "No Image or Text")

    print(f"\n── STRUCTURAL FAILURES (always high priority) ──────────────")
    print(f"  Untagged (tagged=0):           {untagged:>4}  ({untagged/total*100:.1f}%)")
    print(f"  Image Only (no text layer):    {image_only:>4}  ({image_only/total*100:.1f}%)")
    print(f"  No Image or Text:              {no_content:>4}  ({no_content/total*100:.1f}%)")
    print(f"  Approved exporter (auto-pass): {approved_count:>4}  ({approved_count/total*100:.1f}%)")

    # ── Violations/page distribution ──────────────────────────────────────
    print(f"\n── Errors/Page DISTRIBUTION ────────────────────────────────")
    brackets = [
        ("0  (fully compliant)",       lambda e: e == 0),
        ("1–3   (minor)",              lambda e: 1 <= e <= 3),
        ("4–9   (moderate)",           lambda e: 4 <= e <= 9),
        ("10–19 (serious)",            lambda e: 10 <= e <= 19),
        ("20–49 (very serious)",       lambda e: 20 <= e <= 49),
        ("50+   (severe)",             lambda e: e >= 50),
    ]
    for label, fn in brackets:
        count = sum(1 for e in errors_per_page if fn(e))
        bar   = "█" * min(40, int(count / total * 40))
        print(f"  {label:<28} {count:>4}  ({count/total*100:5.1f}%)  {bar}")

    # ── Forms ──────────────────────────────────────────────────────────────
    forms_total      = sum(has_form_vals)
    forms_any_viol   = sum(1 for ep, hf in zip(errors_per_page, has_form_vals) if hf and ep > 0)
    forms_gt3        = sum(1 for ep, hf in zip(errors_per_page, has_form_vals) if hf and ep > 3)

    print(f"\n── FORMS ───────────────────────────────────────────────────")
    print(f"  Has form:                      {forms_total:>4}  ({forms_total/total*100:.1f}%)")
    print(f"  Form + any violation:          {forms_any_viol:>4}  ({forms_any_viol/total*100:.1f}%)")
    print(f"  Form + Errors/Page > 3:        {forms_gt3:>4}  ({forms_gt3/total*100:.1f}%)")

    # ── Threshold comparison ───────────────────────────────────────────────
    print(f"\n── HIGH PRIORITY COUNT AT DIFFERENT Errors/Page THRESHOLDS ─")
    print(f"  (includes untagged + Image Only regardless of threshold)")
    print()

    def count_high(ep_threshold: int, form_threshold: int) -> int:
        flagged = set()
        for i, row in enumerate(rows):
            ep       = errors_per_page[i]
            tagged   = tagged_vals[i]
            tt       = text_types[i]
            has_form = has_form_vals[i]
            approved = approved_vals[i]

            if tagged == 0:
                flagged.add(i); continue
            if tt == "Image Only":
                flagged.add(i); continue
            if approved:
                continue
            if ep > ep_threshold:
                flagged.add(i); continue
            if has_form and ep > form_threshold:
                flagged.add(i)
        return len(flagged)

    thresholds = [
        (1,  1,  "very strict  — any violation at all flags a PDF"),
        (3,  1,  "strict       — current recommendation for ADA"),
        (5,  2,  "moderate"),
        (10, 3,  "lenient"),
        (20, 3,  "current setting (too lenient)"),
        (50, 3,  "very lenient"),
    ]
    print(f"  {'Errors/Page >':>14}  {'Form >':>6}  {'High Priority':>13}  Note")
    print(f"  {'-'*14}  {'-'*6}  {'-'*13}  ----")
    for ep_t, fm_t, note in thresholds:
        n = count_high(ep_t, fm_t)
        marker = "  ← current" if ep_t == 20 else ""
        print(f"  {ep_t:>14}  {fm_t:>6}  {n:>13}  {note}{marker}")

    # ── Recommendation ─────────────────────────────────────────────────────
    print(f"\n── RECOMMENDATION ──────────────────────────────────────────")
    at_3  = count_high(3, 1)
    at_20 = count_high(20, 3)
    print(f"  Current threshold (>20):  {at_20} high priority PDFs")
    print(f"  Recommended  (>3, form>1): {at_3} high priority PDFs")
    print()
    print("  For ADA Title II / PDF/UA compliance, a PDF with >3 errors/page")
    print("  consistently fails WCAG 2.1 AA criteria (missing alt text, broken")
    print("  reading order, unlabelled form fields, missing document structure).")
    print("  Threshold >3 is the most defensible line for 'meaningfully inaccessible'.")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["onedrive", "local"], default="onedrive")
    parser.add_argument("--local-path", metavar="PATH")
    args = parser.parse_args()

    if args.source == "onedrive":
        source_path = Path(config.TEAMS_ONEDRIVE_PATH)
    else:
        if not args.local_path:
            print("ERROR: --local-path required with --source=local")
            sys.exit(1)
        source_path = Path(args.local_path)

    if not source_path.exists():
        print(f"ERROR: path not found: {source_path}")
        sys.exit(1)

    print(f"Reading from: {source_path}\n")
    rows = collect_rows(source_path)
    print(f"\nLoaded {len(rows)} rows across all domains.")
    analyse(rows)


if __name__ == "__main__":
    main()
