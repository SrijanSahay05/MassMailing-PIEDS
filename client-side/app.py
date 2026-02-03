from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import pandas as pd
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from email_sender import send_email
from google_authentication import get_gmail_service
import requests
from requests.exceptions import ConnectionError, Timeout

app = Flask(__name__)
app.secret_key = "your-secret-key-here"  # Change this in production

# Configuration
UPLOAD_FOLDER = "uploads"
HISTORY_FILE = "mailing_history.json"
ALLOWED_EXTENSIONS = {"xlsx", "xls", "csv"}
TEMPLATE_FOLDER = "templates"

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)


@app.context_processor
def inject_auth_status():
    return dict(is_authenticated=os.path.exists("token.json"))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_template(template_path):
    """Load subject and body from a template file."""
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Split on the first occurrence of 'body:'
        subject = None
        body = None
        if "subject:" in content and "body:" in content:
            subject = content.split("subject:", 1)[1].split("body:", 1)[0].strip()
            body = content.split("body:", 1)[1].strip()
        if not subject or not body:
            raise ValueError("Template file must contain both subject and body.")
        return subject, body
    except Exception as e:
        raise e


def get_placeholders(text):
    """Extract placeholders like {name} from text."""
    import re
    if not text:
        return []
    # Find all {variable} patterns
    return list(set(re.findall(r'\{([a-zA-Z0-9_]+)\}', text)))


def load_history():
    """Load mailing history from JSON file."""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading history: {e}")
        return []


def save_history(history):
    """Save mailing history to JSON file."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving history: {e}")


def add_to_history(campaign_data, results):
    """Add a new campaign to the history."""
    history = load_history()

    campaign_record = {
        "id": len(history) + 1,
        "timestamp": datetime.now().isoformat(),
        "campaign_name": campaign_data.get("campaign_name", "Unnamed Campaign"),
        "filename": campaign_data.get("filename"),
        "template_used": campaign_data.get("template_path"),
        "total_emails": campaign_data.get("total_emails", 0),
        "success_count": len([r for r in results if r["status"] == "success"]),
        "error_count": len([r for r in results if r["status"] == "error"]),
        "skipped_count": len([r for r in results if r["status"] == "skipped"]),
        "results_sample": results[:10],  # Store first 10 results for quick preview
        "failed_results": [r for r in results if r["status"] == "error"], # Store ALL failures with full details
        "column_mapping": {
            "email_col": campaign_data.get("email_col"),
            "poc_col": campaign_data.get("poc_col"),
            "designation_col": campaign_data.get("designation_col"),
            "company_col": campaign_data.get("company_col"),
        },
    }

    history.append(campaign_record)
    save_history(history)
    return campaign_record["id"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/home")
def home():
    return render_template("index.html")


@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/draft-editor")
def draft_editor():
    return render_template("draft_editor.html")


@app.route("/api/history")
def get_history():
    """API endpoint to get mailing history."""
    try:
        history = load_history()
        return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/history/<int:campaign_id>")
def get_campaign_details(campaign_id):
    """API endpoint to get details of a specific campaign."""
    try:
        history = load_history()
        campaign = next((c for c in history if c["id"] == campaign_id), None)
        if campaign:
            return jsonify({"success": True, "campaign": campaign})
        else:
            return jsonify({"success": False, "error": "Campaign not found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/test")
def test():
    return jsonify({"status": "ok", "message": "Server is running"})


@app.route("/login")
def login():
    try:
        service = get_gmail_service()
        if service:
            flash("Successfully authenticated with Gmail!", "success")
        else:
            flash("Gmail authentication failed.", "danger")
    except Exception as e:
        flash(f"Login error: {str(e)}", "danger")
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    try:
        if os.path.exists("token.json"):
            os.remove("token.json")
            flash("Successfully logged out (token cleared).", "success")
        else:
            flash("No active session found.", "info")
    except Exception as e:
        flash(f"Logout error: {str(e)}", "danger")
    return redirect(url_for("index"))


@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        print("Upload request received")
        if "excel_file" not in request.files:
            print("No file in request")
            return jsonify({"success": False, "error": "No file selected"})

        file = request.files["excel_file"]
        if file.filename == "":
            print("Empty filename")
            return jsonify({"success": False, "error": "No file selected"})

        print(f"Processing file: {file.filename}")
        if not allowed_file(file.filename):
            return jsonify(
                {
                    "success": False,
                    "error": "Invalid file type. Please upload .xlsx, .xls, or .csv files",
                }
            )

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
                    if pd.isna(value) or (
                        isinstance(value, float) and str(value) == "nan"
                    ):
                        row_dict[col] = None
                    else:
                        row_dict[col] = value
                preview_data.append(row_dict)

            columns = df.columns.tolist()
            print(
                f"Preview data created successfully. Preview rows: {len(preview_data)}"
            )

            response_data = {
                "success": True,
                "filename": filename,
                "preview": preview_data,
                "columns": columns,
                "total_rows": len(df),
            }
            print("Sending response...")
            return jsonify(response_data)
        except Exception as e:
            print(f"Error reading Excel file: {str(e)}")
            return jsonify(
                {"success": False, "error": f"Error reading Excel file: {str(e)}"}
            )

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({"success": False, "error": f"Upload error: {str(e)}"})


def extract_emails(email_str):
    """Find all valid email patterns within a string."""
    if not email_str:
        return []
    import re
    # Robust regex specifically for finding emails in text
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    found = re.findall(email_pattern, str(email_str))
    # Cleanup trailing dots often caught by regex in text contexts
    return [e.rstrip('.') for e in found if e]


@app.route("/api/template-placeholders", methods=["POST"])
def get_template_placeholders():
    try:
        data = request.get_json()
        template_path = data.get("template_path")
        if not template_path:
            return jsonify({"success": False, "error": "No template path provided"})
        
        subject, body = load_template(template_path)
        placeholders = get_placeholders(subject) + get_placeholders(body)
        # Remove duplicates while preserving order
        unique_placeholders = []
        for p in placeholders:
            if p not in unique_placeholders:
                unique_placeholders.append(p)
                
        return jsonify({"success": True, "placeholders": unique_placeholders})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/save-draft", methods=["POST"])
def save_draft():
    try:
        data = request.get_json()
        filename = data.get("filename")
        subject = data.get("subject")
        body = data.get("body")
        
        if not filename or not subject or not body:
            return jsonify({"success": False, "error": "Missing required fields"})
            
        if not filename.endswith(".txt"):
            filename += ".txt"
            
        content = f"subject: {subject}\n\nbody: {body}"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
            
        return jsonify({"success": True, "message": "Draft saved successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/get-draft", methods=["GET"])
def get_draft():
    try:
        filename = request.args.get("filename")
        if not filename:
            return jsonify({"success": False, "error": "No filename provided"})
            
        subject, body = load_template(filename)
        return jsonify({"success": True, "subject": subject, "body": body})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/preview", methods=["POST"])
def preview_emails():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data received"})

        filename = data.get("filename")
        column_mapping = data.get("column_mapping", {})
        template_path = data.get("template_path", "draft_template.txt")
        page = data.get("page", 1)
        per_page = data.get("per_page", 10)

        if not filename:
            return jsonify({"success": False, "error": "No filename provided"})

        # Load template
        try:
            subject_template, body_template = load_template(template_path)
        except Exception as e:
            return jsonify({"success": False, "error": f"Template error: {str(e)}"})

        # Read Excel file
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "File not found"})

        try:
            df = pd.read_excel(filepath)
            # Handle NaN values
            df = df.where(pd.notnull(df), None)
        except Exception as e:
            return jsonify({"success": False, "error": f"Error reading file: {str(e)}"})

        # Normalize columns in DF
        df.columns = [c.lower() for c in df.columns]
        
        # Normalize column mapping values
        normalized_mapping = {k: v.lower() for k, v in column_mapping.items() if v}

        # Check mapped columns exist
        for placeholder, col_name in normalized_mapping.items():
            if col_name and col_name not in df.columns:
                return jsonify(
                    {
                        "success": False,
                        "error": f'Column "{col_name}" not found. Available columns: {df.columns.tolist()}',
                    }
                )
                
        # Fallback for email if not explicitly mapped but 'email address' or 'email' exists
        email_col = normalized_mapping.get("email")
        if not email_col:
             if "email address" in df.columns:
                 email_col = "email address"
             elif "email" in df.columns:
                 email_col = "email"
             else:
                 # If we can't find an email column, we can't send/preview effectively unless we assume one
                 pass 

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
                
                # Dynamic context creation
                context = {}
                for placeholder, col_name in normalized_mapping.items():
                    context[placeholder] = row[col_name] if row[col_name] is not None else ""
                
                # Ensure email is in context if we found an email column
                recipient_emails = []
                if email_col:
                     raw_email = row[email_col]
                     recipient_emails = extract_emails(raw_email)
                     context["email"] = ", ".join(recipient_emails) if recipient_emails else ""

                # Skip rows with missing email if that's critical (it usually is)
                if not recipient_emails:
                    # We might want to show it anyway with an error or just skip?
                    # logic was:
                    # if not recipient_email: continue
                    pass

                try:
                    subject = subject_template.format(**context)
                    body = body_template.format(**context)
                except KeyError as e:
                    return jsonify({"success": False, "error": f"Missing column mapping for placeholder: {e}"})

                # Ensure row_number is a native int
                row_number = int(idx + 1)

                preview_emails.append(
                    {
                        "to": ", ".join(recipient_emails),
                        "subject": str(subject),
                        "body": str(body),  # Full HTML body for proper rendering
                        "row_number": row_number,
                        "context": {k: str(v) for k, v in context.items()} # Sending context for debugging/display
                    }
                )
            except Exception as e:
                # print(e)
                return jsonify(
                    {
                        "success": False,
                        "error": f"Error processing row {int(idx + 1)}: {str(e)}",
                    }
                )

        return jsonify(
            {
                "success": True,
                "preview_emails": preview_emails,
                "total_emails": total_rows,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "per_page": per_page,
                    "start_idx": start_idx + 1,
                    "end_idx": end_idx,
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": f"Preview error: {str(e)}"})


@app.route("/send", methods=["POST"])
def send_emails():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data received"})

        filename = data.get("filename")
        column_mapping = data.get("column_mapping", {})
        template_path = data.get("template_path", "draft_template.txt")
        cc = data.get("cc")

        if not filename:
            return jsonify({"success": False, "error": "No filename provided"})

        # Load template
        try:
            subject_template, body_template = load_template(template_path)
        except Exception as e:
            return jsonify({"success": False, "error": f"Template error: {str(e)}"})

        # Read Excel file
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "File not found"})

        try:
            df = pd.read_excel(filepath)
            # Handle NaN values
            df = df.where(pd.notnull(df), None)
        except Exception as e:
            return jsonify({"success": False, "error": f"Error reading file: {str(e)}"})

        # Normalize columns in DF
        df.columns = [c.lower() for c in df.columns]
        
        # Normalize column mapping
        normalized_mapping = {k: v.lower() for k, v in column_mapping.items() if v}

        # Check columns exist
        for placeholder, col_name in normalized_mapping.items():
            if col_name and col_name not in df.columns:
                return jsonify(
                    {
                        "success": False,
                        "error": f'Column "{col_name}" not found. Available columns: {df.columns.tolist()}',
                    }
                )

        # Determine email column
        email_col = normalized_mapping.get("email")
        if not email_col:
             if "email address" in df.columns:
                 email_col = "email address"
             elif "email" in df.columns:
                 email_col = "email"
        
        # Determine name for sending context (e.g. "recipient_name")
        # We'll use 'poc_name' if available as the recipient name, or just split email or empty
        poc_col = normalized_mapping.get("poc_name")
        if not poc_col and "poc name" in df.columns:
            poc_col = "poc name"

        # Get Gmail service
        try:
            gmail_service = get_gmail_service()
            if not gmail_service:
                return jsonify(
                    {"success": False, "error": "Gmail authentication failed"}
                )
            # Get sender's email from Gmail profile
            user_profile = gmail_service.users().getProfile(userId="me").execute()
            user_email = user_profile["emailAddress"]
        except Exception as e:
            return jsonify(
                {"success": False, "error": f"Gmail authentication error: {str(e)}"}
            )

        # Send emails
        results = []
        total_to_send = len(df)
        
        # Identify required company col for CRM tracking if possible
        company_col = normalized_mapping.get("company")
        if not company_col and "company name" in df.columns:
            company_col = "company name"

        for idx, row in df.iterrows():
            try:
                raw_emails = row[email_col] if email_col else ""
                recipient_emails = extract_emails(raw_emails)
                
                # Context for template
                context = {}
                for placeholder, col_name in normalized_mapping.items():
                    context[placeholder] = row[col_name] if row[col_name] is not None else ""
                
                # Ensure email is in context (joined by comma for display if needed)
                if email_col:
                    context["email"] = ", ".join(recipient_emails) if recipient_emails else ""

                # Skip rows with missing email
                if not recipient_emails:
                    results.append(
                        {
                            "email": "N/A",
                            "status": "skipped",
                            "message": "No email address provided",
                            "progress": f"{idx+1}/{total_to_send}",
                            "debug": f"Row {idx+1}: Skipped (no email)"
                        }
                    )
                    continue

                subject = subject_template.format(**context)
                body = body_template.format(**context)
                
                poc_name = row[poc_col] if poc_col else (context.get("name") or context.get("poc_name") or "")
                company_val = row[company_col] if company_col else (context.get("company") or "")

                # Loop through each email in the cell
                for email_addr in recipient_emails:
                    try:
                        # Send the email
                        sent_message_object = send_email(
                            gmail_service,
                            email_addr,
                            poc_name,
                            subject,
                            body,
                            is_html=True,
                            cc_emails=cc,
                            index=idx+1,
                            total=total_to_send
                        )
                        thread_id = sent_message_object.get('threadId') if sent_message_object else None

                        crm_data = {
                            "email": email_addr,
                            "poc_name": poc_name,
                            "company": company_val,
                            "sender": user_email,
                            "assigned_to": user_email,
                            "status": "CONTACTED",
                            "gmail_thread_id": thread_id
                        }
                        
                        # CRM submission logic (omitted for brevity)
                        results.append({
                            "email": email_addr,
                            "status": "success",
                            "id": f"{idx+1}_{email_addr}"
                        })
                    except Exception as e_addr:
                        results.append({
                            "email": email_addr,
                            "status": "error",
                            "message": str(e_addr),
                            "progress": f"{idx+1}/{total_to_send}",
                            "debug": f"Row {idx+1}: Exception for {email_addr}: {e_addr}",
                            "context": context
                        })
                
            except Exception as e:
                results.append(
                    {
                        "email": raw_emails or "N/A",
                        "status": "error",
                        "message": str(e),
                        "progress": f"{idx+1}/{total_to_send}",
                        "debug": f"Row {idx+1}: Exception processing row: {e}",
                        "context": context if 'context' in locals() else {}
                    }
                )

        success_count = len([r for r in results if r["status"] == "success"])
        error_count = len([r for r in results if r["status"] == "error"])
        skipped_count = len([r for r in results if r["status"] == "skipped"])
        
        # Save history (simplified mapping for history)
        campaign_record_id = add_to_history({
            "campaign_name": f"Campaign - {filename}",
            "filename": filename,
            "template_path": template_path,
            "total_emails": total_to_send,
            "email_col": email_col,
            "poc_col": poc_col,
            "designation_col": normalized_mapping.get('designation'),
            "company_col": company_col
        }, results)

        return jsonify(
            {
                "success": True,
                "results": results,
                "summary": {
                    "total": len(results),
                    "success": success_count,
                    "errors": error_count,
                    "skipped": skipped_count,
                    "campaign_id": campaign_record_id
                },
            }
        )

    except (ConnectionError, Timeout) as e:
        return jsonify({"success": False, "error": "CRM server is unreachable or timed out. Please check the backend server.", "details": str(e)}), 503
    except Exception as e:
        return jsonify({"success": False, "error": f"Send error: {str(e)}"})


@app.route("/templates")
def list_templates():
    try:
        templates = []
        for filename in os.listdir("."):
            if filename.endswith(".txt"):
                templates.append(filename)
        return jsonify(templates)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/dashboard')
def dashboard():
    from flask import request
    # Try to get the authenticated user's email from Gmail
    try:
        gmail_service = get_gmail_service()
        if not gmail_service:
            flash('You must authenticate with Gmail to view your dashboard.', 'danger')
            return redirect(url_for('index'))
        user_profile = gmail_service.users().getProfile(userId="me").execute()
        user_email = user_profile["emailAddress"]
    except Exception as e:
        user_email = None
        contacts = []
        flash(f'Error fetching user email: {str(e)}', 'danger')
        return render_template('dashboard.html', contacts=contacts, user_email=user_email)
    # Pagination
    page = int(request.args.get('page', 1))
    page_size = 10
    crm_error = None
    try:
        resp = requests.get('https://crm.srijansahay05.in/api/crm/contacts/list/', params={'user_email': user_email, 'page': page, 'page_size': page_size}, timeout=6)
        data = resp.json() if resp.status_code == 200 else {}
        contacts = data.get('results', [])
        total = data.get('total', 0)
        total_pages = data.get('total_pages', 1)
    except (ConnectionError, Timeout) as e:
        contacts = []
        total = 0
        total_pages = 1
        crm_error = 'CRM server is unreachable or timed out. Please check the backend server.'
    except Exception as e:
        contacts = []
        total = 0
        total_pages = 1
        flash(f'Error fetching contacts: {str(e)}', 'danger')
    # Format sent_at for display
    def format_sent_at(val):
        if not val:
            return "-"
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(val)
            return dt.strftime("%H:%M || %d/%m/%Y")
        except Exception:
            return str(val)
    for c in contacts:
        c['sent_at_formatted'] = format_sent_at(c.get('sent_at'))
    return render_template('dashboard.html', contacts=contacts, user_email=user_email, page=page, total_pages=total_pages, crm_error=crm_error)


@app.errorhandler(ConnectionError)
def handle_connection_error(e):
    return jsonify({"success": False, "error": "CRM server is unreachable. Please check the backend server."}), 503

@app.errorhandler(Timeout)
def handle_timeout_error(e):
    return jsonify({"success": False, "error": "CRM server timed out. Please check the backend server."}), 504


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8001)
