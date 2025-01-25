# feature/controllers/contact_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db_dependency
from app.api.deps import get_current_user
from ..schemas.contact_schema import ContactSyncRequest, ContactSyncResponse
from ..services.contact_service import ContactService
from app.core.error_handler import create_success_response

router = APIRouter(tags=["contacts"])


@router.post("/sync", response_model=ContactSyncResponse)
async def sync_contacts(
        request: ContactSyncRequest,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db_dependency)
):
    """
    Synchronize user's phone contacts and discover matches
    """
    try:
        contact_service = ContactService()
        matches = await contact_service.sync_contacts(
            db,
            current_user.id,
            request.contacts
        )

        return create_success_response(
            message="Contacts synced successfully",
            data=matches
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )