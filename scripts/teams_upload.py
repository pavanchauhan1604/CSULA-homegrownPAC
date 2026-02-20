"""Copy the latest Excel accessibility report for each domain into the OneDrive
folder that is synced to your Teams channel. OneDrive handles uploading to
Teams automatically — no API or authentication required.

Folder behaviour
----------------
* If the domain subfolder does not yet exist in the OneDrive folder, it is
  created so the file lands in the right place.
* All other files already in the folder are untouched.
* If you re-scan the same domain on the same day the new timestamped file is
  added alongside the previous one (different filenames).

Usage
-----
    # Copy reports for all configured domains:
    python scripts/teams_upload.py

    # Copy reports for specific domains only:
    python scripts/teams_upload.py --domains www.calstatela.edu_admissions libguides.calstatela.edu
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import config


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

def _check_config() -> Path:
    """Return the validated OneDrive root path."""
    raw = getattr(config, "TEAMS_ONEDRIVE_PATH", "")
    if not raw:
        print("ERROR: TEAMS_ONEDRIVE_PATH is not set in config.py")
        sys.exit(1)
    onedrive = Path(raw)
    if not onedrive.exists():
        print(f"ERROR: OneDrive path does not exist: {onedrive}")
        print("Make sure your Teams channel Files folder is synced via OneDrive.")
        sys.exit(1)
    return onedrive


# ---------------------------------------------------------------------------
# Copy logic
# ---------------------------------------------------------------------------

def copy_domain(onedrive_path: Path, domain: str) -> bool:
    """Copy the latest local .xlsx for *domain* into the OneDrive folder.

    Returns True on success, False if no local report was found.
    """
    xlsx_path = config.get_excel_report_path(domain, prefer_latest=True)
    if not xlsx_path or not Path(xlsx_path).exists():
        print(f"  [SKIP] No local Excel report found for: {domain}")
        return False

    folder_name = config.get_domain_folder_name(domain)
    dest_folder = onedrive_path / folder_name
    dest_folder.mkdir(exist_ok=True)

    dest = dest_folder / xlsx_path.name
    shutil.copy2(xlsx_path, dest)

    print(f"  {xlsx_path.name}")
    print(f"    → .../{folder_name}/")
    print(f"  [OK]")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    onedrive_path = _check_config()

    parser = argparse.ArgumentParser(
        description="Copy the latest Excel scan reports to the OneDrive/Teams folder.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--domains",
        nargs="+",
        metavar="DOMAIN",
        help="Domain name(s) to copy. Defaults to all domains in config.DOMAINS.",
    )
    args = parser.parse_args()

    domains = args.domains or config.DOMAINS

    print(f"OneDrive folder: {onedrive_path}")
    print(f"Copying {len(domains)} domain report(s)…\n")

    successes = 0
    failures = 0

    for domain in domains:
        print(f"▶ {domain}")
        try:
            if copy_domain(onedrive_path, domain):
                successes += 1
            else:
                failures += 1
        except Exception as exc:
            print(f"  [ERROR] {exc}")
            failures += 1
        print()

    print("─" * 55)
    print(f"Done.  Copied: {successes}  |  Skipped / failed: {failures}")
    print("OneDrive will sync the new files to Teams in the background.")


if __name__ == "__main__":
    main()
