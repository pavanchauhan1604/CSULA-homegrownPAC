#!/usr/bin/env python3
"""Fix duplicate rows in drupal_pdf_files and add a unique index.

Why:
- The pipeline stores (pdf_uri, parent_uri) pairs.
- If duplicates exist, downstream steps can balloon (e.g., 40k+ rows) and run forever.

What this does:
1) Creates a timestamped backup copy of the DB file (unless --no-backup).
2) Deletes duplicate rows in drupal_pdf_files, keeping the smallest id for each
   (drupal_site_id, pdf_uri, parent_uri) key.
3) Creates a UNIQUE index on (drupal_site_id, pdf_uri, parent_uri) to prevent
   future duplicates.

Safe defaults:
- Use --dry-run to see how many rows would be deleted.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def _backup_db(db_path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_suffix(db_path.suffix + f".backup.{timestamp}")
    shutil.copy2(db_path, backup_path)
    return backup_path


def _get_duplicate_count(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    # count rows - count distinct keys => duplicates beyond 1
    row_count = cur.execute("SELECT COUNT(*) FROM drupal_pdf_files").fetchone()[0]
    distinct_count = cur.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT 1
            FROM drupal_pdf_files
            GROUP BY drupal_site_id, pdf_uri, parent_uri
        )
        """
    ).fetchone()[0]
    return int(row_count - distinct_count)


def _dedupe(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    before = cur.execute("SELECT changes()").fetchone()[0]
    cur.execute(
        """
        DELETE FROM drupal_pdf_files
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM drupal_pdf_files
            GROUP BY drupal_site_id, pdf_uri, parent_uri
        );
        """
    )
    # SQLite changes() returns count for last statement
    deleted = cur.execute("SELECT changes()").fetchone()[0]
    return int(deleted)


def _create_unique_index(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_drupal_pdf_files_unique
        ON drupal_pdf_files (drupal_site_id, pdf_uri, parent_uri);
        """
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Deduplicate drupal_pdf_files and add a unique index")
    parser.add_argument(
        "--db",
        default="drupal_pdfs.db",
        help="Path to SQLite DB (default: drupal_pdfs.db)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report duplicates; do not modify DB",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a timestamped backup copy of the DB",
    )

    args = parser.parse_args()
    db_path = Path(args.db)

    if not db_path.exists():
        raise SystemExit(f"DB not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        dupes = _get_duplicate_count(conn)
        print(f"Duplicates (rows beyond unique site/pdf/parent keys): {dupes}")

        if args.dry_run:
            return 0

        if dupes == 0:
            print("No duplicates found; ensuring unique index exists...")
            _create_unique_index(conn)
            conn.commit()
            return 0

        if not args.no_backup:
            backup_path = _backup_db(db_path)
            print(f"Backup created: {backup_path}")

        print("Deleting duplicates...")
        deleted = _dedupe(conn)
        print(f"Deleted rows: {deleted}")

        print("Creating unique index...")
        _create_unique_index(conn)

        conn.commit()
        print("Done.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
