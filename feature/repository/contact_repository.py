# feature/repository/contact_repository.py
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.contact import ContactRegistry

class ContactRepository:
    @staticmethod
    async def get_contact_by_phone(db: Session, owner_id: int, phone_number: str) -> Optional[ContactRegistry]:
        return db.query(ContactRegistry).filter(
            ContactRegistry.owner_id == owner_id,
            ContactRegistry.phone_number == phone_number
        ).first()

    @staticmethod
    async def create_contact(db: Session, contact_data: dict) -> ContactRegistry:
        contact = ContactRegistry(**contact_data)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact

    @staticmethod
    async def update_contact(db: Session, contact: ContactRegistry, update_data: dict) -> ContactRegistry:
        for key, value in update_data.items():
            setattr(contact, key, value)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact