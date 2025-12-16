#!/usr/bin/env python3
"""Automated Email Sender for PDF Accessibility Reports.

This script sends personalized PDF accessibility reports to website managers
using Outlook Desktop automation (COM).

Important:
- Windows-only (requires Outlook desktop + pywin32).
- SMTP sending has been removed from this project.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.communication.communications import build_emails
from src.communication.outlook_sender import OutlookSendOptions, send_emails_batch_outlook
import config


def _is_windows() -> bool:
    return sys.platform.startswith("win")


def _safe_email_filename(value: str) -> str:
    return value.replace("@", "_at_").replace(".", "_")


def print_results_summary(results: dict):
    print("\n" + "=" * 80)
    print("📊 Email Sending Summary")
    print("=" * 80)

    sent = results.get("sent", [])
    failed = results.get("failed", [])
    saved = results.get("saved", [])
    total = results.get("total", 0)

    print(f"\n✅ Sent/created: {len(sent)} email(s)")
    if sent:
        for email in sent:
            print(f"   • {email}")

    if saved:
        print(f"\n💾 Saved .msg: {len(saved)} file(s)")
        for path_str in saved:
            print(f"   • {path_str}")

    if failed:
        print(f"\n❌ Failed: {len(failed)} email(s)")
        for failure in failed:
            print(f"   • {failure.get('email')}")
            print(f"     Error: {failure.get('error')}")

    print(f"\n📈 Total: {total} email(s)")
    print("=" * 80)


def main():
    print("=" * 80)
    print("📧 PDF Accessibility Email Sender (Outlook - Windows)")
    print("=" * 80)
    
    # Check if email sending is enabled
    if not config.ENABLE_EMAIL_SENDING:
        print("\n⚠️  Email sending is disabled in config.py")
        print("   Set ENABLE_EMAIL_SENDING = True to enable")
        return

    if not _is_windows():
        print("\n❌ Outlook automation is Windows-only.")
        print("   Run this script on a Windows machine with Outlook Desktop installed and signed in.")
        return

    print("\n📡 Delivery Method: Outlook (Windows COM)")
    print("   Requires: Windows + Outlook desktop + pywin32")
    print(f"   Save as .msg: {'Yes' if getattr(config, 'OUTLOOK_SAVE_AS_MSG', False) else 'No'}")
    print(f"   Display only: {'Yes' if getattr(config, 'OUTLOOK_DISPLAY_ONLY', False) else 'No'}")
    if getattr(config, 'OUTLOOK_SENT_ON_BEHALF_OF', None):
        print(f"   Sent on behalf of: {config.OUTLOOK_SENT_ON_BEHALF_OF}")
    if getattr(config, "EMAIL_DRY_RUN", False):
        print("\n🧪 DRY RUN MODE ENABLED")
        print("   Outlook emails will NOT actually be sent/saved (testing only)")
    
    print("=" * 80)
    
    # Generate emails
    print("\n📝 Building email reports...")
    emails = build_emails()
    
    if not emails:
        print("\n⚠️  No emails generated - no users have PDFs requiring review.")
        return
    
    print(f"✅ Generated {len(emails)} email report(s)")
    
    # Confirm before sending
    if not getattr(config, "EMAIL_DRY_RUN", False):
        print("\n" + "=" * 80)
        print("⚠️  IMPORTANT: You are about to send emails to the following recipients:")
        print("=" * 80)
        for _, recipient_email in emails:
            print(f"   • {recipient_email}")
        
        print("\n" + "=" * 80)
        response = input("Do you want to proceed with sending? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("\n❌ Email sending cancelled by user")
            return
    
    outlook_options = OutlookSendOptions(
        subject=config.EMAIL_SUBJECT,
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
    
    # Print summary
    print_results_summary(results)
    
    # Save email copies (HTML) for manual review
    print("\n" + "=" * 80)
    print("💾 Saving email copies for manual review/sending...")
    print("=" * 80)

    if getattr(config, "SAVE_EMAIL_COPIES", False):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        for idx, (html_content, recipient_email) in enumerate(emails, 1):
            base_filename = f"{timestamp}_{idx}_{_safe_email_filename(recipient_email)}"
            html_filepath = config.EMAIL_COPIES_DIR / f"{base_filename}.html"
            with open(html_filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"   ✅ Email #{idx} ({recipient_email}):")
            print(f"      🌐 {base_filename}.html")

        print(f"\n📁 All files saved in: {config.EMAIL_COPIES_DIR.absolute()}/")
        print("\n📋 How to use:")
        print("   • .html files: Open in browser, copy content, paste into email")
    else:
        print("   (SAVE_EMAIL_COPIES is disabled)")
    
    # Final summary
    print("\n" + "=" * 80)
    if getattr(config, "EMAIL_DRY_RUN", False):
        print("🧪 DRY RUN COMPLETE - No actual emails were sent")
    else:
        print("✅ EMAIL SENDING COMPLETE")
        if results['failed']:
            print(f"   {len(results['sent'])} sent, {len(results['failed'])} failed")
        else:
            print(f"   All {len(results['sent'])} emails sent successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
