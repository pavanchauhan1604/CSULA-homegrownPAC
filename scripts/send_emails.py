#!/usr/bin/env python3
"""Send pre-generated HTML email drafts from OneDrive domain folders via Outlook COM.

Each domain folder in OneDrive contains:
  - The latest Excel report  ({domain}-{timestamp}.xlsx)
  - One draft per assigned employee  ({employee_id}_draft.html)

This script discovers every draft, looks up the recipient email from
employees.csv, attaches the latest Excel from the same domain folder,
and sends via Outlook COM — no database access required.

Important:
- Windows-only (requires Outlook desktop + pywin32).
- Run sharepoint_sync.py first to generate the drafts.

Usage
-----
    python scripts/send_emails.py           # prompts before sending
    python scripts/send_emails.py --force   # skips confirmation prompt
"""

import argparse
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import config
from src.communication.communications import _display_domain
from src.communication.outlook_sender import OutlookSendOptions, send_emails_batch_outlook


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_windows() -> bool:
    return sys.platform.startswith("win")


def load_employees(csv_path: Path) -> dict:
    """Returns {employee_id: {first_name, last_name, email}}.

    employees.csv format (with header row):
        Full Name, Employee ID, Email
    """
    employees = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if not row or not row[1].strip():
                continue
            parts = row[0].strip().split(" ", 1)
            employees[row[1].strip()] = {
                "first_name": parts[0],
                "last_name": parts[1] if len(parts) > 1 else "",
                "email": row[2].strip() if len(row) > 2 else "",
            }
    return employees


def find_latest_xlsx(folder: Path):
    """Return the most recently modified .xlsx in folder (ignoring ~$ lock files)."""
    candidates = [p for p in folder.glob("*.xlsx") if not p.name.startswith("~$")]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def folder_to_domain_display(folder_name: str) -> str:
    """Best-effort conversion of an OneDrive folder name to a display label.

    Tries to match against config.DOMAINS first for accuracy, then falls back
    to simple character replacement.
    """
    for domain in config.DOMAINS:
        if config.get_domain_folder_name(domain) == folder_name:
            return _display_domain(domain)
    return folder_name.replace("-", ".").replace("_", "/")


# ---------------------------------------------------------------------------
# Draft discovery
# ---------------------------------------------------------------------------

def discover_emails(onedrive_path: Path, employees: dict) -> list:
    """Scan OneDrive domain folders for *_draft.html files.

    Returns a list of 4-tuples:
        (html_content, recipient_email, [attachments], subject)
    """
    emails = []
    base_subject = getattr(config, "EMAIL_SUBJECT", "PDF Accessibility Report")

    for domain_folder in sorted(onedrive_path.iterdir()):
        if not domain_folder.is_dir():
            continue

        draft_files = sorted(domain_folder.glob("*_draft.html"))
        if not draft_files:
            continue

        latest_xlsx = find_latest_xlsx(domain_folder)
        attachments = [str(latest_xlsx)] if latest_xlsx else []

        display = folder_to_domain_display(domain_folder.name)
        subject = f"{base_subject} - {display}"

        for draft_file in draft_files:
            # Filename convention: {employee_id}_draft.html
            employee_id = draft_file.stem.replace("_draft", "")
            employee = employees.get(employee_id)
            if not employee:
                print(f"  [WARN] Employee '{employee_id}' not in employees.csv — skipping {draft_file.name}")
                continue

            html_content = draft_file.read_text(encoding="utf-8")
            recipient_email = employee["email"]
            if not recipient_email:
                print(f"  [WARN] No email address for employee '{employee_id}' — skipping")
                continue

            emails.append((html_content, recipient_email, attachments, subject))

    return emails


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def print_results_summary(results: dict) -> None:
    print("\n" + "=" * 80)
    print("Email Sending Summary")
    print("=" * 80)

    sent = results.get("sent", [])
    failed = results.get("failed", [])
    saved = results.get("saved", [])
    total = results.get("total", 0)

    print(f"\nSent / created : {len(sent)} email(s)")
    for email in sent:
        print(f"   • {email}")

    if saved:
        print(f"\nSaved .msg     : {len(saved)} file(s)")
        for path_str in saved:
            print(f"   • {path_str}")

    if failed:
        print(f"\nFailed         : {len(failed)} email(s)")
        for failure in failed:
            print(f"   • {failure.get('email')}")
            print(f"     Error: {failure.get('error')}")

    print(f"\nTotal          : {total} email(s)")
    print("=" * 80)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send pre-generated PDF accessibility email drafts via Outlook."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt and send immediately.",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("PDF Accessibility Email Sender (reads drafts from OneDrive)")
    print("=" * 80)

    if not config.ENABLE_EMAIL_SENDING:
        print("\nEmail sending is disabled in config.py (ENABLE_EMAIL_SENDING = False)")
        return

    if not _is_windows():
        print("\nOutlook automation is Windows-only.")
        print("Run this script on a Windows machine with Outlook Desktop installed and signed in.")
        return

    # Validate OneDrive path
    raw = getattr(config, "TEAMS_ONEDRIVE_PATH", "")
    if not raw:
        print("ERROR: TEAMS_ONEDRIVE_PATH is not set in config.py")
        sys.exit(1)
    onedrive_path = Path(raw)
    if not onedrive_path.exists():
        print(f"ERROR: OneDrive path does not exist: {onedrive_path}")
        sys.exit(1)

    # Load employee lookup
    employees = load_employees(config.EMPLOYEES_CSV)

    # Discover drafts
    print(f"\nScanning for email drafts in: {onedrive_path}")
    emails = discover_emails(onedrive_path, employees)

    if not emails:
        print("\nNo email drafts found. Run sharepoint_sync.py first.")
        return

    print(f"\nFound {len(emails)} email draft(s) to send")

    if getattr(config, "EMAIL_DRY_RUN", False):
        print("\nDRY RUN MODE — emails will not actually be sent")
    else:
        print("\n" + "=" * 80)
        print("Recipients:")
        for html, recipient, attachments, subject in emails:
            print(f"   • {recipient}  [{subject}]")
            if attachments:
                for att in attachments:
                    print(f"     Attachment: {Path(att).name}")
        print("=" * 80)

        if not args.force:
            response = input("\nProceed with sending? (yes/no): ").strip().lower()
            if response not in ("yes", "y"):
                print("\nCancelled.")
                return

    outlook_options = OutlookSendOptions(
        subject=getattr(config, "EMAIL_SUBJECT", "PDF Accessibility Report"),
        sent_on_behalf_of=getattr(config, "OUTLOOK_SENT_ON_BEHALF_OF", None),
        save_as_msg=getattr(config, "OUTLOOK_SAVE_AS_MSG", False),
        msg_output_dir=getattr(config, "OUTLOOK_MSG_DIR", None),
        display_only=getattr(config, "OUTLOOK_DISPLAY_ONLY", False),
    )

    results = send_emails_batch_outlook(
        emails=emails,
        options=outlook_options,
        dry_run=getattr(config, "EMAIL_DRY_RUN", False),
    )

    print_results_summary(results)

    print("\n" + "=" * 80)
    if getattr(config, "EMAIL_DRY_RUN", False):
        print("DRY RUN COMPLETE — no actual emails were sent")
    else:
        if results["failed"]:
            print(f"COMPLETE — {len(results['sent'])} sent, {len(results['failed'])} failed")
        else:
            print(f"COMPLETE — all {len(results['sent'])} email(s) sent successfully")
    print("=" * 80)


if __name__ == "__main__":
    main()
