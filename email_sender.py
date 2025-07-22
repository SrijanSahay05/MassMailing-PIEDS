import base64
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError

from google_authentication import get_gmail_service


def send_email(service, recipient_email, recipient_name, subject, body_text, is_html=False):
    """
    Creates and sends an email to a specific recipient.

    Args:
        service: Authorized Gmail API service instance.
        recipient_email: The email address of the recipient.
        recipient_name: The name of the recipient (for personalization).
        subject: The subject line of the email.
        body_text: The content of the email body (plain text or HTML).
        is_html: If True, send as HTML. Otherwise, send as plain text.

    Returns:
        The sent message object if successful, otherwise None.
    """
    try:
        user_profile = service.users().getProfile(userId="me").execute()
        sender_email = user_profile["emailAddress"]

        message = MIMEText(body_text, "html" if is_html else "plain")
        message["to"] = f"{recipient_name} <{recipient_email}>"
        message["from"] = f"PIEDS-ST Mail Merge <{sender_email}>"
        message["subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}

        send_message = (
            service.users().messages().send(userId="me", body=create_message).execute()
        )
        print(
            f"Email sent successfully to {recipient_email}. Message ID: {send_message['id']}"
        )
        return send_message
    except HttpError as error:
        print(f"An error occurred while sending email to {recipient_email}: {error}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


if __name__ == "__main__":
    # Step 1: Authenticate and get the Gmail service object ONCE.
    print("Attempting to authenticate and get Gmail service...")
    gmail_service = get_gmail_service()

    # Step 2: Proceed only if the authentication was successful.
    if gmail_service:
        test_recipient_email = "srijan05sahay@gmail.com"
        test_recipient_name = "Srijan Sahay"
        

        for i in range(1):
            test_subject = f"Hello {test_recipient_name} (Final Script Test) {i}"
            test_body = (
                f"Hi {test_recipient_name},<br><br>"
                "<a href='https://ignite.srijansahay05.in'>Ignite Website</a> :) is up and running"
            )
            print(f"\n=== Sending Test Email {i}===")
            message = MIMEText(test_body, "html")
            message["to"] = f"{test_recipient_name} <{test_recipient_email}>"
            message["from"] = f"P <{gmail_service.users().getProfile(userId='me').execute()['emailAddress']}>"
            message["subject"] = test_subject
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"raw": encoded_message}
            send_message = (
                gmail_service.users().messages().send(userId="me", body=create_message).execute()
            )
            print(f"Email sent successfully to {test_recipient_email}. Message ID: {send_message['id']}")
        print("--------------------------\n")
    else:
        print("Could not create Gmail service. Aborting email send.")

