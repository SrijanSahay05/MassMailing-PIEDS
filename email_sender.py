import base64
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError

from google_authentication import get_gmail_service


def send_email(service, recipient_email, recipient_name, subject, body_text):
    """
    Creates and sends an email to a specific recipient.

    Args:
        service: Authorized Gmail API service instance.
        recipient_email: The email address of the recipient.
        recipient_name: The name of the recipient (for personalization).
        subject: The subject line of the email.
        body_text: The plain text content of the email body.

    Returns:
        The sent message object if successful, otherwise None.
    """
    try:
        user_profile = service.users().getProfile(userId="me").execute()
        sender_email = user_profile["emailAddress"]

        message = MIMEText(body_text)
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
        test_recipient_email = "dronekill1603@gmail.com"
        test_recipient_name = "Srijan Sahay"
        test_subject = f"Hello {test_recipient_name} (Final Script Test)"
        test_body = (
            f"Hi {test_recipient_name},\n\n"
            "This email confirms that the final, corrected versions of the Python scripts are working together perfectly."
        )

        for i in range(1):
            test_subject = f"Hello {test_recipient_name} (Final Script Test) {i}"
            test_body = (
                f"Hi {test_recipient_name},\n\n"
                "This email confirms that the final, corrected versions of the Python scripts are working together perfectly."
            )
            print(f"\n=== Sending Test Email {i}===")
            send_email(
                service=gmail_service,
                recipient_email=test_recipient_email,
                recipient_name=test_recipient_name,
                subject=test_subject,
                body_text=test_body,
            )
        print("--------------------------\n")
    else:
        print("Could not create Gmail service. Aborting email send.")

