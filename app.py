from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import pandas as pd
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from email_sender import send_email
from google_authentication import get_gmail_service

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Configuration
UPLOAD_FOLDER = 'uploads'
HISTORY_FILE = 'mailing_history.json'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
TEMPLATE_FOLDER = 'templates'

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_template(template_path):
    """Load subject and body from a template file."""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Split on the first occurrence of 'body:'
        subject = None
        body = None
        if 'subject:' in content and 'body:' in content:
            subject = content.split('subject:', 1)[1].split('body:', 1)[0].strip()
            body = content.split('body:', 1)[1].strip()
        if not subject or not body:
            raise ValueError('Template file must contain both subject and body.')
        return subject, body
    except Exception as e:
        raise e

def load_history():
    """Load mailing history from JSON file."""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading history: {e}")
        return []

def save_history(history):
    """Save mailing history to JSON file."""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving history: {e}")

def add_to_history(campaign_data, results):
    """Add a new campaign to the history."""
    history = load_history()
    
    campaign_record = {
        'id': len(history) + 1,
        'timestamp': datetime.now().isoformat(),
        'campaign_name': campaign_data.get('campaign_name', 'Unnamed Campaign'),
        'filename': campaign_data.get('filename'),
        'template_used': campaign_data.get('template_path'),
        'total_emails': campaign_data.get('total_emails', 0),
        'success_count': len([r for r in results if r['status'] == 'success']),
        'error_count': len([r for r in results if r['status'] == 'error']),
        'skipped_count': len([r for r in results if r['status'] == 'skipped']),
        'results': results[:10],  # Store first 10 results for preview
        'column_mapping': {
            'email_col': campaign_data.get('email_col'),
            'poc_col': campaign_data.get('poc_col'),
            'designation_col': campaign_data.get('designation_col'),
            'company_col': campaign_data.get('company_col')
        }
    }
    
    history.append(campaign_record)
    save_history(history)
    return campaign_record['id']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/api/history')
def get_history():
    """API endpoint to get mailing history."""
    try:
        history = load_history()
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/history/<int:campaign_id>')
def get_campaign_details(campaign_id):
    """API endpoint to get details of a specific campaign."""
    try:
        history = load_history()
        campaign = next((c for c in history if c['id'] == campaign_id), None)
        if campaign:
            return jsonify({'success': True, 'campaign': campaign})
        else:
            return jsonify({'success': False, 'error': 'Campaign not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/test')
def test():
    return jsonify({'status': 'ok', 'message': 'Server is running'})

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        print("Upload request received")
        if 'excel_file' not in request.files:
            print("No file in request")
            return jsonify({'success': False, 'error': 'No file selected'})
        
        file = request.files['excel_file']
        if file.filename == '':
            print("Empty filename")
            return jsonify({'success': False, 'error': 'No file selected'})
        
        print(f"Processing file: {file.filename}")
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload .xlsx, .xls, or .csv files'})
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        print(f"File saved to: {filepath}")
        
        # Read and preview the file
        try:
            print("Reading Excel file...")
            df = pd.read_excel(filepath)
            print(f"Excel file read successfully. Shape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            
            # Handle NaN values - replace with None for JSON serialization
            df = df.where(pd.notnull(df), None)
            
            # Convert to records and handle any remaining NaN issues
            preview_data = []
            for idx, row in df.head(5).iterrows():
                row_dict = {}
                for col in df.columns:
                    value = row[col]
                    # Convert NaN to None for JSON serialization
                    if pd.isna(value) or (isinstance(value, float) and str(value) == 'nan'):
                        row_dict[col] = None
                    else:
                        row_dict[col] = value
                preview_data.append(row_dict)
            
            columns = df.columns.tolist()
            print(f"Preview data created successfully. Preview rows: {len(preview_data)}")
            
            response_data = {
                'success': True,
                'filename': filename,
                'preview': preview_data,
                'columns': columns,
                'total_rows': len(df)
            }
            print("Sending response...")
            return jsonify(response_data)
        except Exception as e:
            print(f"Error reading Excel file: {str(e)}")
            return jsonify({'success': False, 'error': f'Error reading Excel file: {str(e)}'})
    
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'error': f'Upload error: {str(e)}'})

@app.route('/preview', methods=['POST'])
def preview_emails():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'})
            
        filename = data.get('filename')
        email_col = data.get('email_col', 'email address')
        poc_col = data.get('poc_col', 'poc name')
        designation_col = data.get('designation_col', 'designation')
        company_col = data.get('company_col', 'company name')
        template_path = data.get('template_path', 'draft_template.txt')
        page = data.get('page', 1)
        per_page = data.get('per_page', 10)
        
        if not filename:
            return jsonify({'success': False, 'error': 'No filename provided'})
        
        # Load template
        try:
            subject_template, body_template = load_template(template_path)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Template error: {str(e)}'})
        
        # Read Excel file
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'})
            
        try:
            df = pd.read_excel(filepath)
            # Handle NaN values
            df = df.where(pd.notnull(df), None)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Error reading file: {str(e)}'})
        
        # Normalize columns
        df.columns = [c.lower() for c in df.columns]
        email_col = email_col.lower()
        poc_col = poc_col.lower()
        designation_col = designation_col.lower()
        company_col = company_col.lower()
        
        # Check columns exist
        for col in [email_col, poc_col, designation_col, company_col]:
            if col not in df.columns:
                return jsonify({'success': False, 'error': f'Column "{col}" not found. Available columns: {df.columns.tolist()}'})
        
        # Calculate pagination
        total_rows = len(df)
        total_pages = (total_rows + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_rows)
        
        # Generate preview emails for current page
        preview_emails = []
        for idx in range(start_idx, end_idx):
            try:
                row = df.iloc[idx]
                recipient_email = row[email_col] or ''
                poc_name = row[poc_col] or ''
                designation = row[designation_col] or ''
                company = row[company_col] or ''
                
                # Skip rows with missing email
                if not recipient_email:
                    continue
                
                subject = subject_template.format(
                    poc_name=poc_name, designation=designation, company=company
                )
                body = body_template.format(
                    poc_name=poc_name, designation=designation, company=company, email=recipient_email
                )
                
                preview_emails.append({
                    'to': recipient_email,
                    'poc_name': poc_name,
                    'designation': designation,
                    'company': company,
                    'subject': subject,
                    'body': body,  # Full HTML body for proper rendering
                    'row_number': idx + 1
                })
            except Exception as e:
                return jsonify({'success': False, 'error': f'Error processing row {idx+1}: {str(e)}'})
        
        return jsonify({
            'success': True,
            'preview_emails': preview_emails,
            'total_emails': total_rows,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'per_page': per_page,
                'start_idx': start_idx + 1,
                'end_idx': end_idx
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Preview error: {str(e)}'})

@app.route('/send', methods=['POST'])
def send_emails():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'})
            
        filename = data.get('filename')
        email_col = data.get('email_col', 'email address')
        poc_col = data.get('poc_col', 'poc name')
        designation_col = data.get('designation_col', 'designation')
        company_col = data.get('company_col', 'company name')
        template_path = data.get('template_path', 'draft_template.txt')
        campaign_name = data.get('campaign_name', f'Campaign {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        
        if not filename:
            return jsonify({'success': False, 'error': 'No filename provided'})
        
        # Load template
        try:
            subject_template, body_template = load_template(template_path)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Template error: {str(e)}'})
        
        # Read Excel file
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'})
            
        try:
            df = pd.read_excel(filepath)
            # Handle NaN values
            df = df.where(pd.notnull(df), None)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Error reading file: {str(e)}'})
        
        # Normalize columns
        df.columns = [c.lower() for c in df.columns]
        email_col = email_col.lower()
        poc_col = poc_col.lower()
        designation_col = designation_col.lower()
        company_col = company_col.lower()
        
        # Check columns exist
        for col in [email_col, poc_col, designation_col, company_col]:
            if col not in df.columns:
                return jsonify({'success': False, 'error': f'Column "{col}" not found. Available columns: {df.columns.tolist()}'})
        
        # Get Gmail service
        try:
            gmail_service = get_gmail_service()
            if not gmail_service:
                return jsonify({'success': False, 'error': 'Gmail authentication failed'})
        except Exception as e:
            return jsonify({'success': False, 'error': f'Gmail authentication error: {str(e)}'})
        
        # Send emails
        results = []
        for idx, row in df.iterrows():
            try:
                recipient_email = row[email_col] or ''
                poc_name = row[poc_col] or ''
                designation = row[designation_col] or ''
                company = row[company_col] or ''
                
                # Skip rows with missing email
                if not recipient_email:
                    results.append({
                        'email': 'N/A',
                        'status': 'skipped',
                        'message': 'No email address provided'
                    })
                    continue
                
                subject = subject_template.format(
                    poc_name=poc_name, designation=designation, company=company
                )
                body = body_template.format(
                    poc_name=poc_name, designation=designation, company=company, email=recipient_email
                )
                
                send_email(
                    gmail_service,
                    recipient_email,
                    poc_name,
                    subject,
                    body,
                    is_html=True
                )
                
                results.append({
                    'email': recipient_email,
                    'status': 'success',
                    'message': 'Email sent successfully'
                })
                
            except Exception as e:
                results.append({
                    'email': recipient_email or 'N/A',
                    'status': 'error',
                    'message': str(e)
                })
        
        success_count = len([r for r in results if r['status'] == 'success'])
        error_count = len([r for r in results if r['status'] == 'error'])
        skipped_count = len([r for r in results if r['status'] == 'skipped'])
        
        # Prepare campaign data for history
        campaign_data = {
            'filename': filename,
            'template_path': template_path,
            'total_emails': len(df),
            'email_col': email_col,
            'poc_col': poc_col,
            'designation_col': designation_col,
            'company_col': company_col,
            'campaign_name': campaign_name
        }
        
        # Add to history
        campaign_id = add_to_history(campaign_data, results)
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total': len(results),
                'success': success_count,
                'errors': error_count,
                'skipped': skipped_count
            },
            'campaign_id': campaign_id,
            'campaign_name': campaign_name
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Send error: {str(e)}'})

@app.route('/templates')
def list_templates():
    try:
        templates = []
        for filename in os.listdir('.'):
            if filename.endswith('.txt'):
                templates.append(filename)
        return jsonify(templates)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000) 
    