#!/usr/bin/env python3
"""Windows-only email sender using Outlook COM automation.

This mirrors the legacy approach used in the SF State project:
- Drive the locally installed Outlook desktop client via COM.
- Works with modern auth/MFA because Outlook is already signed in.

Notes:
- This only works on Windows.
- Requires pywin32 (win32com + pythoncom).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class OutlookSendOptions:
    subject: str
    sent_on_behalf_of: Optional[str] = None
    save_as_msg: bool = False
    msg_output_dir: Optional[Path] = None
    display_only: bool = False


def _is_windows() -> bool:
    import sys

    return sys.platform.startswith("win")


def _safe_filename(value: str) -> str:
    import re

    value = value.strip()
    value = re.sub(r"[\\/:\"*?<>|]+", "_", value)
    value = re.sub(r"\s+", "_", value)
    return value[:180] if len(value) > 180 else value


def _require_windows_and_pywin32() -> Tuple[bool, str]:
    if not _is_windows():
        return (
            False,
            "Outlook COM sending is only supported on Windows (pywin32 + Outlook desktop).",
        )

    try:
        # Optional dependency (Windows only)
        import win32com.client  # type: ignore[import-not-found]  # noqa: F401
        import pythoncom  # type: ignore[import-not-found]  # noqa: F401
    except Exception as e:
        return (
            False,
            "pywin32 is required for Outlook COM sending. Install with: pip install pywin32. "
            f"Import error: {e}",
        )

    return (True, "")


def send_email_outlook(
    recipient_email: str,
    html_content: str,
    options: OutlookSendOptions,
) -> Tuple[bool, str, Optional[Path]]:
    """Send (or save) a single email using Outlook.

    Returns:
        (success, message, msg_path)
    """

    ok, msg = _require_windows_and_pywin32()
    if not ok:
        return (False, msg, None)

    import pythoncom  # type: ignore[import-not-found]
    import win32com.client  # type: ignore[import-not-found]

    pythoncom.CoInitialize()
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail_item = outlook.CreateItem(0)  # 0 = olMailItem

        mail_item.To = recipient_email
        mail_item.Subject = options.subject
        mail_item.BodyFormat = 2  # 2 = olFormatHTML
        mail_item.HTMLBody = html_content

        if options.sent_on_behalf_of:
            # Requires Exchange permission: "Send on behalf" or "Send As"
            mail_item.SentOnBehalfOfName = options.sent_on_behalf_of

        saved_path: Optional[Path] = None
        if options.save_as_msg:
            out_dir = options.msg_output_dir
            if out_dir is None:
                return (False, "save_as_msg=True but msg_output_dir is not set.", None)

            out_dir.mkdir(parents=True, exist_ok=True)
            filename = _safe_filename(f"{recipient_email}_{options.subject}") + ".msg"
            saved_path = out_dir / filename
            # 3 = olMSG
            mail_item.SaveAs(str(saved_path), 3)

        if options.display_only:
            mail_item.Display()
            return (True, f"✅ Displayed draft in Outlook for {recipient_email}", saved_path)

        if not options.save_as_msg:
            mail_item.Send()
            return (True, f"✅ Sent via Outlook to {recipient_email}", saved_path)

        return (True, f"✅ Saved Outlook .msg for {recipient_email}", saved_path)

    except Exception as e:
        return (False, f"❌ Outlook COM error: {e}", None)
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


def send_emails_batch_outlook(
    emails: Iterable[Tuple[str, str]],
    options: OutlookSendOptions,
    dry_run: bool = False,
) -> dict:
    """Send multiple emails via Outlook with a results summary."""

    emails_list: List[Tuple[str, str]] = list(emails)

    results = {
        "sent": [],
        "failed": [],
        "total": len(emails_list),
        "saved": [],
    }

    if dry_run:
        print("\n" + "=" * 80)
        print("🧪 DRY RUN MODE - No emails will be sent/saved")
        print("=" * 80)

    print(f"\n📧 Outlook sending {len(emails_list)} email(s)...")
    print("=" * 80)

    for idx, (html_content, recipient_email) in enumerate(emails_list, 1):
        print(f"\n[{idx}/{len(emails_list)}] To: {recipient_email}")

        if dry_run:
            print("   🧪 DRY RUN - Would create Outlook email")
            results["sent"].append(recipient_email)
            continue

        success, message, saved_path = send_email_outlook(
            recipient_email=recipient_email,
            html_content=html_content,
            options=options,
        )

        print(f"   {message}")
        if success:
            results["sent"].append(recipient_email)
            if saved_path is not None:
                results["saved"].append(str(saved_path))
        else:
            results["failed"].append({"email": recipient_email, "error": message})

    return results
