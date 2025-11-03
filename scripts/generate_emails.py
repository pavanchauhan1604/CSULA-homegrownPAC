#!/usr/bin/env python3
"""
Generate HTML email reports for all users with PDFs.
This script creates HTML files in output/emails/ directory.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.communication.communications import build_emails
import re

def sanitize_email_for_filename(email):
    """Convert email to safe filename format."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', email.replace('@', '_at_'))

def main():
    print("=" * 80)
    print("📧 Generating Email Reports")
    print("=" * 80)
    
    emails = build_emails()
    
    if not emails:
        print("\n⚠️  No emails generated - no users have PDFs requiring review.")
        return
    
    output_dir = Path("output/emails")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n✅ Generated {len(emails)} email(s)")
    print("-" * 80)
    
    for idx, (html_content, recipient_email) in enumerate(emails, 1):
        # Create safe filename
        safe_filename = f"email_{sanitize_email_for_filename(recipient_email)}.html"
        output_path = output_dir / safe_filename
        
        # Save HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"{idx}. {recipient_email}")
        print(f"   📄 Saved to: {output_path}")
        print()
    
    print("=" * 80)
    print("✅ All emails generated successfully!")
    print("=" * 80)
    print(f"\n📂 Location: {output_dir.absolute()}")
    print(f"\n💡 To preview: open {output_dir.absolute()}/*.html")

if __name__ == "__main__":
    main()
