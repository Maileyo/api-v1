import httpx
from app.controller.auth_controller import get_access_token
from fastapi import HTTPException

GRAPH_API_URL = "https://graph.microsoft.com/v1.0"
BATCH_URL = f"{GRAPH_API_URL}/$batch"

async def get_recent_emails(user_id: str, email_id: str, page: int, page_size: int):
    ACCESS_TOKEN = await get_access_token(user_id, email_id)
    try:
        # Calculate the number of emails to skip
        skip = (page - 1) * page_size
        
        # Define the batch request payload with pagination
        batch_request_body = {
            "requests": [
                {
                    "id": "1",
                    "method": "GET",
                    "url": f"/me/mailFolders/inbox/messages?$top={page_size}&$skip={skip}&$select=subject,receivedDateTime,from,toRecipients,isRead"
                }
            ]
        }

        # Set headers with Authorization token
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        # Make the batch request to Microsoft Graph API asynchronously using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(BATCH_URL, json=batch_request_body, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            batch_response = response.json()
            email_metadata = batch_response["responses"][0]["body"]["value"]
            return email_metadata
        else:
            return {"error": f"Failed to fetch emails. Status code: {response.status_code}"}
    except Exception as e:
        print(f"Error during email fetching process: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {e}")
