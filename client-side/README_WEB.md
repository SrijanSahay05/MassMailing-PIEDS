# PIEDS Mass Mailing System - Web Frontend

**Made by Srijan Sahay**

A modern web interface for the PIEDS Mass Mailing System that provides an intuitive way to upload Excel files, preview emails, and send bulk emails through a browser.

## Features

- **Drag & Drop File Upload**: Easy Excel file upload with drag & drop support
- **Real-time Preview**: Preview your data and email content before sending
- **Column Mapping**: Automatically detect and map Excel columns
- **Email Preview**: See exactly how your emails will look before sending
- **Progress Tracking**: Real-time feedback on email sending progress
- **Results Summary**: Detailed results of your email campaign

## Installation

### 1. Install Dependencies
```bash
pip install -r web_requirements.txt
```

### 2. Ensure Required Files
Make sure you have:
- `email_sender.py` (your existing email sending module)
- `google_authentication.py` (your existing Gmail authentication)
- `draft_template.txt` (your email template)
- `credentials.json` (Google Cloud credentials)

### 3. Run the Application
```bash
python app.py
```

The application will start on `http://localhost:8000`

## Usage

### Step 1: Upload Excel File
1. Open your browser and go to `http://localhost:8000`
2. Drag and drop your Excel file or click "Browse Files"
3. Supported formats: `.xlsx`, `.xls`, `.csv`

### Step 2: Configure Settings
1. The system will automatically detect your Excel columns
2. Map the columns to:
   - Email Address
   - POC Name
   - Designation
   - Company Name
3. Select your email template
4. Preview your data

### Step 3: Preview and Send
1. Review email previews for the first 3 contacts
2. Click "Send All Emails" to start the campaign
3. Monitor progress and view results

## File Structure

```
├── app.py                 # Flask web application
├── templates/
│   └── index.html        # Main web interface
├── uploads/              # Temporary file storage
├── web_requirements.txt  # Python dependencies
├── email_sender.py       # Your existing email module
├── google_authentication.py  # Your existing auth module
├── draft_template.txt    # Your email template
└── credentials.json      # Google Cloud credentials
```

## Technical Details

### Backend (Flask)
- **File Upload**: Secure file handling with validation
- **Data Processing**: Pandas for Excel file processing
- **Email Integration**: Uses your existing Gmail API setup
- **Real-time Feedback**: JSON API endpoints for AJAX requests

### Frontend (HTML/JavaScript)
- **Modern UI**: Bootstrap 5 for responsive design
- **Interactive**: Drag & drop, real-time previews
- **User-friendly**: Step-by-step wizard interface
- **Progress Tracking**: Loading states and result summaries

## Security Features

- **File Validation**: Only allows Excel/CSV files
- **Secure Filenames**: Uses Werkzeug's secure_filename
- **Input Sanitization**: Validates all user inputs
- **Error Handling**: Comprehensive error messages

## Troubleshooting

### Common Issues

1. **Gmail Authentication Error**
   - Ensure `credentials.json` is in the project directory
   - Check that Gmail API is enabled in Google Cloud Console

2. **File Upload Issues**
   - Verify file format (.xlsx, .xls, .csv)
   - Check file size (should be reasonable)
   - Ensure file is not corrupted

3. **Column Mapping Issues**
   - Verify column names in your Excel file
   - Check for extra spaces or special characters
   - Ensure required columns exist

### Error Messages

- **"Column not found"**: Check your Excel column names
- **"Template file not found"**: Ensure `draft_template.txt` exists
- **"Gmail authentication failed"**: Check your credentials

## Development

### Adding New Features

1. **New File Formats**: Add to `ALLOWED_EXTENSIONS` in `app.py`
2. **Additional Columns**: Modify the column mapping logic
3. **Custom Templates**: Add template selection options

### Customization

- **Styling**: Modify CSS in `templates/index.html`
- **Validation**: Add custom validation rules in `app.py`
- **Email Logic**: Extend the email sending functionality

## Support

For issues or questions, contact the PIEDS Student Team.

---

**Made with ❤️ by Srijan Sahay** 