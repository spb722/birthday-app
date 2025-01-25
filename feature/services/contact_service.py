# feature/services/contact_service.py
from typing import List
from sqlalchemy.orm import Session
from ..models.contact import ContactRegistry
from ..schemas.contact_schema import ContactInfo, UserMatchInfo
from ..repository.contact_repository import ContactRepository
from app.models.user import User


class ContactService:
    def __init__(self):
        self.repository = ContactRepository()

    async def sync_contacts(
            self,
            db: Session,
            owner_id: int,
            contacts: List[ContactInfo]
    ) -> List[UserMatchInfo]:
        try:
            matches = []
            for contact in contacts:
                # Check for existing contact or create new one
                existing_contact = await self.repository.get_contact_by_phone(
                    db, owner_id, contact.phone_number
                )

                if existing_contact:
                    if existing_contact.contact_name != contact.name:
                        await self.repository.update_contact(
                            db,
                            existing_contact,
                            {"contact_name": contact.name}
                        )
                else:
                    existing_contact = await self.repository.create_contact(db, {
                        "owner_id": owner_id,
                        "phone_number": contact.phone_number,
                        "contact_name": contact.name
                    })

                # Check if contact is a registered user
                user = db.query(User).filter(User.phone == contact.phone_number).first()
                if user:
                    await self.repository.update_contact(
                        db,
                        existing_contact,
                        {"registered_user_id": user.id}
                    )
                    matches.append(UserMatchInfo(
                        contact_name=contact.name,
                        user_id=str(user.id),
                        profile_picture=user.profile_picture_url,
                        mutual_friends=await self._count_mutual_friends(db, owner_id, user.id)
                    ))

            return matches

        except Exception as e:
            raise ValueError(f"Contact sync failed: {str(e)}")

    async def _count_mutual_friends(self, db: Session, user_id1: int, user_id2: int) -> int:
        # Get contacts for both users who are registered users
        user1_contacts = db.query(ContactRegistry.registered_user_id).filter(
            ContactRegistry.owner_id == user_id1,
            ContactRegistry.registered_user_id.isnot(None)
        ).all()

        user2_contacts = db.query(ContactRegistry.registered_user_id).filter(
            ContactRegistry.owner_id == user_id2,
            ContactRegistry.registered_user_id.isnot(None)
        ).all()

        # Convert to sets for intersection
        user1_contact_ids = {contact[0] for contact in user1_contacts}
        user2_contact_ids = {contact[0] for contact in user2_contacts}

        return len(user1_contact_ids & user2_contact_ids)