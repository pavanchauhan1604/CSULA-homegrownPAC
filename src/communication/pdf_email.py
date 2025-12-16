"""DEPRECATED legacy file.

This module contains an older Windows-only Outlook COM example kept for reference.

Use scripts/send_emails.py for the supported Outlook automation workflow.
"""

# Original Windows-only implementation below
# DO NOT USE - Not compatible with macOS or Linux

"""
import win32com.client as win32
import pythoncom
import time

from communications import build_emails

emails = build_emails()


def generate_email(html_content, reciever):
    print("html_content", html_content)

    # Ensure Outlook is correctly registered and accessible via COM
    pythoncom.CoInitialize()

    print("1. Attempting to create Outlook application instance...")
    outlook = win32.Dispatch('Outlook.Application')
    print("Outlook application instance created.")

    # Get the MAPI namespace
    print("2. Getting MAPI namespace...")
    namespace = outlook.GetNamespace("MAPI")
    print("MAPI namespace obtained.")

    # Wait for a short period to ensure everything is initialized
    time.sleep(2)

    # Create a new mail item
    print("3. Creating new mail item...")
    mail_item  = outlook.CreateItem(0)  # 0: olMailItem
    print("Mail item created.")

    # Set the email properties
    mail_item.Subject = "Drupal PDF Accessibility Conformance Project"
    mail_item.BodyFormat = 2  # 2: olFormatHTML
    mail_item.HTMLBody = html_content
    mail_item.To = "fontaine@sfsu.edu"
    print("Email properties set.")

    # Save the email as an MSG file
    save_path = r"C:\Users\913678186\IdeaProjects\sf_state_pdf_website_scan\emails\email.msg"
    # mail.SaveAs(save_path, 3)  # 3: olMSG
    print("Sending")
    mail_item.Send()
    # print(f"Email saved as: {save_path}")
    print("Complete")

    pythoncom.CoUninitialize()


for email in emails:
    generate_email(email[0], email[1])
"""
