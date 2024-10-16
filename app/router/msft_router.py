from fastapi import APIRouter, Query
from app.service.emails_fetch.msft_service import get_recent_emails

router = APIRouter()

@router.get("/api/v1/msft/recent-emails")
async def fetch_emails(user_id: str = Query(...), email_id: str = Query(...), page: int = Query(1, ge=1), page_size: int = Query(25, ge=1)):
    emails = await get_recent_emails(user_id, email_id, page, page_size)
    return emails
