# Email Sending Guide

## Overview
After generating PDF accessibility reports, you need to send HTML emails to site managers. This guide covers different methods.

---

## 📧 Method 1: Python SMTP (Recommended)

### Quick Start
```bash
python3 scripts/send_emails.py
```

### Cal State LA Email Setup

#### For Office 365 (Outlook/Cal State LA Email)
- **SMTP Server**: `smtp.office365.com`
- **Port**: `587`
- **Username**: Your full Cal State LA email (e.g., `pchauha5@calstatela.edu`)
- **Password**: Your Cal State LA email password
- **Security**: TLS (handled automatically)

#### For Gmail (Alternative)
- **SMTP Server**: `smtp.gmail.com`
- **Port**: `587`
- **Username**: Your Gmail address
- **Password**: **App Password** (not regular password)
  - Go to: https://myaccount.google.com/apppasswords
  - Create app password for "Mail"
  - Use this 16-character password instead

### Example Usage
```bash
$ python3 scripts/send_emails.py

Choose mode:
  1. Send emails (requires SMTP setup)
  2. Test mode (save to files only)

Choice (1/2): 1
SMTP Server: smtp.office365.com
SMTP Port: 587
Your Cal State LA email: pchauha5@calstatela.edu
SMTP Username: pchauha5@calstatela.edu
SMTP Password: [hidden]

1. Sending to pchauha5@calstatela.edu...
   ✅ Sent successfully!
```

---

## 📋 Method 2: Manual Email (Simplest)

### Steps:
1. **Open the HTML file**
   ```bash
   open output/emails/email_pchauha5_at_calstatela_edu.html
   ```

2. **Copy the content**
   - Browser opens with formatted email
   - Press `Cmd+A` to select all
   - Press `Cmd+C` to copy

3. **Paste in email client**
   - Open Gmail/Outlook web or desktop
   - Compose new email
   - Click in message body and press `Cmd+V`
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

### Never Commit Passwords!
Create a `.env` file for credentials:

```bash
# .env (add to .gitignore!)
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=pchauha5@calstatela.edu
SMTP_PASSWORD=your_password_here
```

Then use python-dotenv:
```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
import os

load_dotenv()
smtp_config = {
    'server': os.getenv('SMTP_SERVER'),
    'username': os.getenv('SMTP_USERNAME'),
    'password': os.getenv('SMTP_PASSWORD')
}
```

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
- **Authentication failed**: Check username/password, may need app password

---

## 🚀 Production Deployment

### For ongoing use:
1. Set up dedicated service account (e.g., `pdf-reports@calstatela.edu`)
2. Use that account's SMTP credentials
3. Store credentials securely (environment variables or secrets manager)
4. Schedule workflow with cron or Task Scheduler
5. Enable email sending as final step

### Example Cron Job (monthly):
```bash
# Edit crontab
crontab -e

# Run on 1st of every month at 9 AM
0 9 1 * * cd /Users/pavan/Work/CSULA-homegrownPAC && ./scripts/run_workflow.sh --auto-send
```

---

## 📞 Support

For Cal State LA IT email configuration:
- **IT Help Desk**: https://www.calstatela.edu/its
- **Email Support**: itsupport@calstatela.edu

For SMTP issues, contact your campus IT department.
