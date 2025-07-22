import pandas as pd
from email_sender import send_email
from google_authentication import get_gmail_service

def load_template(template_path):
    """Load subject and body from a template file."""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        subject = None
        body_lines = []
        in_body = False
        for line in lines:
            if line.strip().lower().startswith('subject:'):
                subject = line.partition(':')[2].strip()
            elif line.strip().lower().startswith('body:'):
                in_body = True
            elif in_body:
                body_lines.append(line)
        body = '\n'.join(body_lines).strip()
        if not subject or not body:
            raise ValueError('Template file must contain both subject and body.')
        return subject, body
    except Exception as e:
        print(f"[ERROR] Failed to load template: {e}")
        raise

def send_bulk_emails_from_excel(
    excel_path,
    email_col,
    poc_col,
    designation_col,
    company_col,
    subject_template,
    body_template
):
    """
    Reads an Excel file and sends personalized emails to all listed addresses.
    """
    try:
        print(f"[INFO] Reading Excel file: {excel_path}")
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"[ERROR] Failed to read Excel file: {e}")
        return
    # Normalize columns for case-insensitive matching
    df.columns = [c.lower() for c in df.columns]
    email_col = email_col.lower()
    poc_col = poc_col.lower()
    designation_col = designation_col.lower()
    company_col = company_col.lower()
    # Check if columns exist
    for col in [email_col, poc_col, designation_col, company_col]:
        if col not in df.columns:
            print(f"[ERROR] Column '{col}' not found in Excel file. Available columns: {df.columns.tolist()}")
            return
    try:
        gmail_service = get_gmail_service()
        if not gmail_service:
            print("[ERROR] Could not authenticate with Gmail. Aborting.")
            return
    except Exception as e:
        print(f"[ERROR] Gmail authentication failed: {e}")
        return
    for idx, row in df.iterrows():
        try:
            recipient_email = row[email_col]
            poc_name = row[poc_col]
            designation = row[designation_col]
            company = row[company_col]
            subject = subject_template.format(
                poc_name=poc_name, designation=designation, company=company
            )
            body = body_template.format(
                poc_name=poc_name, designation=designation, company=company, email=recipient_email
            )
            print(f"[INFO] Sending email to {recipient_email} (POC: {poc_name}, Designation: {designation}, Company: {company})")
            send_email(
                gmail_service,
                recipient_email,
                poc_name,
                subject,
                body,
                is_html=True
            )
        except Exception as e:
            print(f"[ERROR] Failed to send email to row {idx+1}: {e}")
            continue

def main():
    print("=== Bulk Email Sender from Excel ===")
    try:
        excel_path = input("Enter path to Excel file [default: template.xlsx]: ").strip() or "template.xlsx"
        email_col = input("Enter column heading for Email address [default: email address]: ").strip() or "email address"
        poc_col = input("Enter column heading for POC name [default: poc name]: ").strip() or "poc name"
        designation_col = input("Enter column heading for Designation [default: designation]: ").strip() or "designation"
        company_col = input("Enter column heading for Company name [default: company name]: ").strip() or "company name"
        template_path = input("Enter path to draft template file [default: draft_template.txt]: ").strip() or "draft_template.txt"
        subject_template, body_template = load_template(template_path)
        print("\nYou can use {poc_name}, {designation}, {company}, {email} in your templates.")
    except Exception as e:
        print(f"[ERROR] Error during input or template loading: {e}")
        return
    send_bulk_emails_from_excel(
        excel_path,
        email_col,
        poc_col,
        designation_col,
        company_col,
        subject_template,
        body_template
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}")
