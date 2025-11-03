#!/usr/bin/env python3
"""
Open and prepare HTML email reports for manual sending.
Emails are generated as HTML files that you can copy/paste into your email client.
"""

import sys
import re
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.communication.communications import build_emails


def sanitize_email_for_filename(email):
    """Convert email to safe filename format."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', email.replace('@', '_at_'))


def main():
    print("=" * 80)
    print("📧 Email Report Generator")
    print("=" * 80)
    
    # Generate emails
    emails = build_emails()
    
    if not emails:
        print("\n⚠️  No emails generated - no users have PDFs requiring review.")
        return
    
    output_dir = Path("output/emails")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n✅ Generated {len(emails)} email report(s)")
    print("=" * 80)
    
    # Save all emails
    email_files = []
    for idx, (html_content, recipient_email) in enumerate(emails, 1):
        safe_filename = f"email_{sanitize_email_for_filename(recipient_email)}.html"
        output_path = output_dir / safe_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        email_files.append((recipient_email, output_path))
        print(f"\n{idx}. {recipient_email}")
        print(f"   📄 {output_path}")
    
    # Show instructions
    print("\n" + "=" * 80)
    print("📋 How to Send Emails (Manual Method)")
    print("=" * 80)
    print("\nFor each recipient:")
    print("  1. Open the HTML file in browser (see paths above)")
    print("  2. Select all content (Cmd+A)")
    print("  3. Copy (Cmd+C)")
    print("  4. Open Cal State LA webmail or Outlook")
    print("  5. Compose new email to recipient")
    print("  6. Paste in message body (Cmd+V)")
    print("  7. Subject: 'PDF Accessibility Report - Cal State LA'")
    print("  8. Send!")
    print("\n✅ All formatting, colors, and tables will paste perfectly!")
    
    # Open first email as example
    if email_files:
        print("\n" + "=" * 80)
        print(f"🌐 Opening first email in browser...")
        print("=" * 80)
        import subprocess
        subprocess.run(['open', str(email_files[0][1])])
        print(f"\n✅ Opened: {email_files[0][1]}")
        print(f"   For: {email_files[0][0]}")
        
        if len(email_files) > 1:
            print(f"\n� {len(email_files) - 1} more email(s) saved in: {output_dir}/")
            print(f"   Open them manually to send to other recipients.")


if __name__ == "__main__":
    main()
