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
                # First clean the contact phone number by removing any non-digit characters
                cleaned_contact_number = ''.join(filter(str.isdigit, contact.phone_number))

                # Find all users (we'll filter them in Python)
                users = db.query(User).filter(User.phone.isnot(None)).all()
                matched_user = None

                for user in users:
                    # Clean the stored phone number
                    cleaned_stored_number = ''.join(filter(str.isdigit, user.phone))

                    # Skip if either number is too short (e.g., less than 8 digits)
                    if len(cleaned_contact_number) < 8 or len(cleaned_stored_number) < 8:
                        continue

                    # Try exact match first
                    if cleaned_contact_number == cleaned_stored_number:
                        matched_user = user
                        break

                    # If no exact match, try suffix matching with longer number
                    if len(cleaned_contact_number) > len(cleaned_stored_number):
                        if cleaned_contact_number.endswith(cleaned_stored_number):
                            matched_user = user
                            break
                    else:
                        if cleaned_stored_number.endswith(cleaned_contact_number):
                            matched_user = user
                            break

                # Rest of the code remains same
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

                if matched_user:
                    await self.repository.update_contact(
                        db,
                        existing_contact,
                        {"registered_user_id": matched_user.id}
                    )
                    matches.append(UserMatchInfo(
                        contact_name=contact.name,
                        user_id=str(matched_user.id),
                        profile_picture=matched_user.profile_picture_url,
                        mutual_friends=await self._count_mutual_friends(db, owner_id, matched_user.id),
                        matched_phone=matched_user.phone,  # Added matched user's phone
                        input_phone=contact.phone_number,  # Added input phone number
                        first_name=matched_user.first_name  # Added first name
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