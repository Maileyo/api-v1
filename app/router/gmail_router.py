from fastapi import APIRouter, Query
from app.service.emails_fetch.gmail_service import fetch_emails

router = APIRouter()

@router.get("/api/v1/gmail/recent-emails")
async def fetch_recent_emails(user_id: str = Query(...), email_id: str = Query(...), page_size: int = Query(10, ge=1), page_token: str = Query(None)):
    """
    API endpoint to fetch emails with pagination.
    """
    emails = await fetch_emails(user_id, email_id, page_size, page_token)
    return emails