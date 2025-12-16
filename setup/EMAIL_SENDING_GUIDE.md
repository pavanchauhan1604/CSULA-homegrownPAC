# Email Sending Guide

## Overview
After generating PDF accessibility reports, you need to send HTML emails to site managers. This guide covers different methods.

---

## 🪟 Method 1: Windows Outlook Automation (Recommended)

Use this if Office 365 SMTP AUTH is disabled (e.g., `535 5.7.139`) and you have access to a Windows PC with Outlook Desktop.

**Requirements**
- Windows
- Outlook Desktop installed and signed in to the sending mailbox
- `pywin32` installed in the Python environment used on Windows (installed via `requirements.txt`, or run: `python -m pip install pywin32`)

**How it works**
- The script controls Outlook via COM to create/send messages.
- This typically works with MFA because Outlook is already authenticated.

**Enable it** (in `config.py`)
- This project uses Outlook automation only (SMTP has been removed).
- Optional:
    - `OUTLOOK_SAVE_AS_MSG = True` to save `.msg` drafts instead of sending
    - `OUTLOOK_DISPLAY_ONLY = True` to open drafts for review
    - `OUTLOOK_SENT_ON_BEHALF_OF = "..."` only if you have Exchange permissions


## 📋 Method 2: Manual Email (Simplest)

### Steps:
1. **Open the HTML file**
   ```bash
   open output/emails/email_pchauha5_at_calstatela_edu.html
   ```

2. **Copy the content**
   - Browser opens with formatted email
    - Press `Cmd+A` (macOS) or `Ctrl+A` (Windows) to select all
    - Press `Cmd+C` (macOS) or `Ctrl+C` (Windows) to copy

3. **Paste in email client**
   - Open Gmail/Outlook web or desktop
   - Compose new email
    - Click in message body and press `Cmd+V` (macOS) or `Ctrl+V` (Windows)
   - The HTML will paste with all formatting intact!

4. **Send**
   - Add recipient
   - Subject: "PDF Accessibility Report - Cal State LA"
   - Send!

**Pros**: Simple, no configuration needed
**Cons**: Manual process for each email

---

## 🔧 Method 3: Automation with Email Service

### Using SendGrid, Mailgun, or AWS SES
For sending many emails, use a transactional email service:

```python
# Example with SendGrid
import sendgrid
from sendgrid.helpers.mail import Mail

def send_via_sendgrid(recipient, html_content, api_key):
    message = Mail(
        from_email='noreply@calstatela.edu',
        to_emails=recipient,
        subject='PDF Accessibility Report',
        html_content=html_content
    )
    sg = sendgrid.SendGridAPIClient(api_key)
    sg.send(message)
```

**Pros**: Scalable, reliable, tracking
**Cons**: Requires service account and budget

---

## 🎯 Integration with Workflow

### Automatic Email Sending After Analysis

Update `run_workflow.sh` to include email sending:

```bash
# At the end of run_workflow.sh, add:

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7: Send Email Reports"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

read -p "Do you want to send emails now? (y/n): " send_emails

if [[ "$send_emails" == "y" ]]; then
    python3 scripts/send_emails.py
else
    echo "Emails saved to: output/emails/"
    echo "Run 'python3 scripts/send_emails.py' when ready to send"
fi
```

---

## 🔒 Security Best Practices

### Never Commit Credentials

- Keep any mailbox-related settings (e.g., shared mailbox “send on behalf” addresses) out of version control if they are sensitive.
- This project does not use SMTP credentials.

---

## ✅ Testing Before Sending

### Preview Emails
```bash
# Generate and open all emails
python3 scripts/generate_emails.py
open output/emails/*.html
```

### Send Test Email First
```bash
# Modify recipient to your own email for testing
# Then run send_emails.py in test mode
python3 scripts/send_emails.py
# Choose option 2 for test mode
```

---

## 📊 Email Delivery Verification

### Check if emails are being received:
1. Send a test email to yourself first
2. Check spam/junk folder
3. Verify HTML renders correctly
4. Click PDF links to ensure they work
5. Confirm colors and formatting are correct

### Common Issues:
- **Email in spam**: Add sender to address book
- **HTML not rendering**: Some email clients block external CSS
- **Links broken**: Ensure PDF URLs are publicly accessible
- **Outlook sending fails**: Ensure Outlook Desktop is installed, signed in, and you have any required “send on behalf” permissions

---

## 🚀 Production Deployment

### For ongoing use:
1. Set up dedicated service account (e.g., `pdf-reports@calstatela.edu`)
2. Ensure Outlook Desktop is configured for that account on a Windows machine
3. Schedule the workflow using Windows Task Scheduler
4. Enable email sending as final step

---

## 📞 Support

For Cal State LA IT email configuration:
- **IT Help Desk**: https://www.calstatela.edu/its
- **Email Support**: itsupport@calstatela.edu

For Outlook automation issues, contact your campus IT department.
