# Mass Mailing Script for PIEDS Student Team

**Made by Srijan Sahay**

This is a Python-based mass mailing script designed for the PIEDS Student Team at BITS Pilani. It allows you to send personalized, beautifully formatted emails in bulk using data from an Excel sheet.

---

## Features
- Send personalized HTML emails to multiple recipients
- Uses Gmail API for secure sending
- Reads recipient data from an Excel file
- Supports custom email templates with placeholders
- Works on both Mac and Windows

---

## Prerequisites
- Python 3.8 or higher
- A Gmail account with API access
- [Google Cloud credentials](https://developers.google.com/gmail/api/quickstart/python) (`credentials.json`)

---

## Installation

### 1. Clone the Repository
```sh
git clone <your-repo-url>
cd MassMailingScript
```

### 2. Install Python Dependencies

#### On Mac/Linux:
```sh
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

#### On Windows:
```sh
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

### 3. Add Google Credentials
- Download your `credentials.json` from Google Cloud Console and place it in the project directory.

---

## Usage

### 1. Prepare Your Excel File
- Make sure your Excel file (e.g., `template.xlsx`) contains columns for email address, POC name, designation, and company name.

### 2. Prepare Your Email Template
- Edit `draft_template.txt` to customize your subject and email body. You can use placeholders like `{poc_name}`, `{company}`, `{designation}`, and `{email}`.

### 3. Run the Script

#### On Mac/Linux:
```sh
python3 main.py
```

#### On Windows:
```sh
py main.py
```

- Follow the interactive prompts to:
  - Enter the path to your Excel file
  - Enter the column headings (or press Enter to use defaults)
  - Enter the path to your draft template file (or press Enter to use `draft_template.txt`)

---

## Notes
- The first time you run the script, a browser window will open for Gmail authentication. Approve access to generate `token.json`.
- All emails are sent using the Gmail API and will appear in your "Sent" folder.
- For best results, use the provided template structure and test with a small batch before sending to all recipients.

---

## License
This project is for internal use by the PIEDS Student Team at BITS Pilani.

---

**Made with ❤️ by Srijan Sahay**