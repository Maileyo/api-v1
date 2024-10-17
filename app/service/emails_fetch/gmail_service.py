from app.controller.auth_controller import get_access_token
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from fastapi import HTTPException

async def get_gmail_service(user_id: str, email_id: str):
    """
    Initialize and return the Gmail service.
    """
    ACCESS_TOKEN = await get_access_token(user_id, email_id)
    credentials = Credentials(token=ACCESS_TOKEN)
    return build('gmail', 'v1', credentials=credentials)


def clean_email_data(email):
    """
    Extract and clean the relevant data from the raw email.

    Args:
    - email: The raw email data from the Gmail API.

    Returns:
    - A dictionary with cleaned email details.
    """
    return {
        "id": email["id"],
        "threadId": email["threadId"],
        "labelIds": email.get("labelIds", []),
        "snippet": email.get("snippet", ""),
        "from": next(header["value"] for header in email["payload"]["headers"] if header["name"] == "From"),
        "to": next(header["value"] for header in email["payload"]["headers"] if header["name"] == "To"),
        "subject": next(header["value"] for header in email["payload"]["headers"] if header["name"] == "Subject"),
        "date": next(header["value"] for header in email["payload"]["headers"] if header["name"] == "Date"),
    }


def create_batch_request(service, messages, callback):
    """
    Create and execute a batch request for the given messages.

    Args:
    - service: The Gmail API service object.
    - messages: List of messages to fetch details for.
    - callback: The callback function to handle the batch responses.

    Returns:
    - A list of fetched emails.
    """
    batch = service.new_batch_http_request()
    for message in messages:
        message_id = message['id']
        print(f"Adding message {message_id} to batch request")
        batch.add(
            service.users().messages().get(userId='me', id=message_id, format='full'),
            callback=callback
        )

    print("Executing batch request")
    batch.execute()


async def fetch_emails(user_id: str, email_id: str, page_size: int, page_token: str = None):
    """
    Fetch Gmail messages and their details in a batch with pagination.

    Args:
    - page_size: The number of emails to fetch per page.
    - page_token: The token to retrieve the next page of emails.

    Returns:
    - A dictionary with the list of cleaned emails and the next page token.
    """
    service = await get_gmail_service(user_id, email_id)

    try:
        # Get the list of message IDs for pagination
        response = service.users().messages().list(userId='me', maxResults=page_size, pageToken=page_token).execute()
        messages = response.get('messages', [])
        next_page_token = response.get('nextPageToken')

        if not messages:
            return {"emails": [], "nextPageToken": None}

        emails = []

        def handle_message_request(request_id, response, exception):
            """Callback function to handle each individual response."""
            if exception:
                print(f"Error fetching message {request_id}: {exception}")
            else:
                emails.append(clean_email_data(response))
                print(f"Fetched and cleaned message: {request_id}")

        # Create and execute the batch request to fetch full email details
        create_batch_request(service, messages, handle_message_request)

        # Return cleaned email data with pagination token
        return {"emails": emails, "nextPageToken": next_page_token}

    except Exception as e:
        print(f"Error during email fetching process: {e}")
        raise Exception(f"Error fetching messages: {e}")
    
async def fetch_emails_from_contact(user_id: str, email_id: str, contact_id: str):
    """
    Fetch emails sent/received from/to a specific email address.
    
    Args:
        user_id (str): Email address of the user.
        email_id (str): Email address of the contact (sender/recipient).
    
    Returns:
        dict: A list of emails and metadata.
    """
    service = await get_gmail_service(user_id, email_id)

    query = f"from:{contact_id} OR to:{contact_id}"

    try:
        # Get the list of messages (filtered by the query)
        response = service.users().messages().list(userId=email_id, q=query).execute()
        messages = response.get('messages', [])
        
        if not messages:
            return {"emails": []}

        emails = []

        def handle_message_request(request_id, response, exception):
            """Callback function to handle each individual response in the batch."""
            if exception:
                print(f"Error fetching message {request_id}: {exception}")
            else:
                emails.append(clean_email_data(response))
                print(f"Fetched message: {request_id}")

        # Create and execute the batch request
        create_batch_request(service, messages, handle_message_request)

        # Return the cleaned emails
        return {"emails": emails}

    except Exception as e:
        print(f"Error during email fetching process: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {e}")
