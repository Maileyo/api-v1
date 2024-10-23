from fastapi import APIRouter, Query
from app.service.emails_fetch.msft_service import get_recent_emails, get_emails_by_contact, get_attachments


router = APIRouter()

@router.get("/api/v1/msft/recent-emails")
async def fetch_emails(user_id: str = Query(...), email_id: str = Query(...), page: int = Query(1, ge=1), page_size: int = Query(25, ge=1)):
    emails = await get_recent_emails(user_id, email_id, page, page_size)
    return emails

@router.get("/api/v1/msft/emails-from")
async def fetch_emails(user_id: str = Query(...), email_id: str = Query(...), contact_email: str = Query(...)):
    emails = await get_emails_by_contact(user_id, email_id, contact_email)
    return emails

@router.get("/api/v1/msft/get-attachment/")
async def get_email_attachments(user_id: str = Query(...), email_id: str = Query(...), message_id: str = Query(...)):
    """
    Get all attachments of a specific email by message ID
    """
    attachments = await get_attachments(user_id, email_id, message_id)
    return attachments