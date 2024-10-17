from fastapi import APIRouter, Query
from app.service.emails_fetch.gmail_service import fetch_emails, fetch_emails_from_contact

router = APIRouter()

@router.get("/api/v1/gmail/recent-emails")
async def fetch_recent_emails(user_id: str = Query(...), email_id: str = Query(...), page_size: int = Query(10, ge=1), page_token: str = Query(None)):
    """
    API endpoint to fetch emails with pagination.
    """
    emails = await fetch_emails(user_id, email_id, page_size, page_token)
    return emails

@router.get("/api/v1/gmail/emails-from")
async def fetch_emails_from(user_id: str = Query(...), email_id: str = Query(...), contact_id: str = Query(...)):
    """
    API endpoint to fetch emails of a user from specific contact. 
    """
    emails = await fetch_emails_from_contact(user_id, email_id, contact_id)
    return emails