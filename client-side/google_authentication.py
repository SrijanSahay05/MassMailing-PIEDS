import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://mail.google.com/",
]

def get_gmail_service():
    """
    Authenticates the user and returns a Gmail API service object.
    Handles the OAuth 2.0 flow and token management.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("No valid credentials found. Starting authentication flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            print("Credentials saved to token.json")

    try:
        service = build("gmail", "v1", credentials=creds)
        print("Authentication successful. Gmail service object created.")
        return service
    except HttpError as error:
        print(f"An error occurred during service creation: {error}")
        return None

if __name__ == "__main__":
    print("Running authentication module directly to check/create token...")
    get_gmail_service()
    print("Authentication check complete. 'token.json' is ready.")

