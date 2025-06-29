# feature/services/contact_service.py
from typing import List, Dict
from sqlalchemy.orm import Session
from ..models.contact import ContactRegistry
from ..schemas.contact_schema import ContactInfo, UserMatchInfo
from ..repository.contact_repository import ContactRepository
from app.models.user import User

class ContactService:
    def __init__(self):
        self.repository = ContactRepository()
        self.chunk_size = 100  # Configurable chunk size
        self.user_batch_size = 5000  # Load users in batches
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Remove all non-digit characters from phone number"""
        return ''.join(filter(str.isdigit, phone))
    
    @staticmethod
    def get_phone_variants(phone: str) -> List[str]:
        """Generate possible phone number variants for matching"""
        normalized = ContactService.normalize_phone(phone)
        variants = [normalized]
        
        # If more than 10 digits, try without country code
        if len(normalized) > 10:
            variants.append(normalized[-10:])  # Last 10 digits
            variants.append(normalized[-9:])   # Last 9 digits
        
        # If exactly 10 digits, try with common country codes
        if len(normalized) == 10:
            variants.append(f"1{normalized}")   # US/Canada
            variants.append(f"91{normalized}")  # India
        
        return variants
    
    def _build_phone_index(self, db: Session) -> Dict[str, User]:
        """Build an efficient phone-to-user lookup map"""
        phone_to_user = {}
        
        # Query users in batches to manage memory
        offset = 0
        while True:
            users = db.query(User).filter(
                User.phone.isnot(None)
            ).offset(offset).limit(self.user_batch_size).all()
            
            if not users:
                break
                
            for user in users:
                normalized = self.normalize_phone(user.phone)
                if len(normalized) >= 8:  # Valid phone length
                    # Index the normalized number
                    phone_to_user[normalized] = user
                    
                    # Also index common variants
                    if len(normalized) > 10:
                        phone_to_user[normalized[-10:]] = user
                        phone_to_user[normalized[-9:]] = user
            
            offset += self.user_batch_size
        
        return phone_to_user
    
    async def _process_contact_chunk(
        self, db: Session, owner_id: int, 
        contacts: List[ContactInfo], 
        phone_to_user: Dict[str, User]
    ) -> List[UserMatchInfo]:
        """Process a chunk of contacts efficiently"""
        matches = []
        contact_updates = []
        
        for contact in contacts:
            matched_user = None
            
            # Try each variant until we find a match
            for variant in self.get_phone_variants(contact.phone_number):
                if variant in phone_to_user:  # O(1) lookup!
                    matched_user = phone_to_user[variant]
                    break
            
            # Prepare bulk update data
            contact_updates.append({
                'owner_id': owner_id,
                'phone_number': contact.phone_number,
                'contact_name': contact.name,
                'registered_user_id': matched_user.id if matched_user else None
            })
            
            # Add to matches if found
            if matched_user:
                matches.append(UserMatchInfo(
                    contact_name=contact.name,
                    user_id=str(matched_user.id),
                    profile_picture=matched_user.profile_picture_url,
                    mutual_friends=0,  # Calculate later in batch
                    matched_phone=matched_user.phone,
                    input_phone=contact.phone_number,
                    first_name=matched_user.first_name
                ))
        
        # Bulk update contact registry
        await self._bulk_upsert_contacts(db, contact_updates)
        
        # Calculate mutual friends if needed
        if matches:
            matches = await self._add_mutual_friends_batch(db, owner_id, matches)
        
        return matches
    
    async def _bulk_upsert_contacts(
        self,
        db: Session,
        contact_updates: List[Dict]
    ) -> None:
        """Efficiently bulk update contact registry"""
        if not contact_updates:
            return
        
        # Get existing contacts
        phone_numbers = [c['phone_number'] for c in contact_updates]
        existing = db.query(ContactRegistry).filter(
            ContactRegistry.owner_id == contact_updates[0]['owner_id'],
            ContactRegistry.phone_number.in_(phone_numbers)
        ).all()
        
        existing_map = {c.phone_number: c for c in existing}
        
        # Separate updates and inserts
        updates = []
        inserts = []
        
        for update in contact_updates:
            if update['phone_number'] in existing_map:
                # Update existing
                contact = existing_map[update['phone_number']]
                contact.contact_name = update['contact_name']
                contact.registered_user_id = update['registered_user_id']
                updates.append(contact)
            else:
                # New contact
                inserts.append(ContactRegistry(**update))
        
        # Bulk operations
        if inserts:
            db.bulk_save_objects(inserts)
        
        # Updates are already tracked by SQLAlchemy
        db.commit()
    
    async def _add_mutual_friends_batch(
        self,
        db: Session,
        owner_id: int,
        matches: List[UserMatchInfo]
    ) -> List[UserMatchInfo]:
        """Calculate mutual friends for all matches in one query"""
        matched_user_ids = [int(match.user_id) for match in matches]
        
        # Single query for all contacts
        contacts = db.query(
            ContactRegistry.owner_id,
            ContactRegistry.registered_user_id
        ).filter(
            ContactRegistry.owner_id.in_([owner_id] + matched_user_ids),
            ContactRegistry.registered_user_id.isnot(None)
        ).all()
        
        # Build contact sets
        contact_map = {}
        for owner, registered in contacts:
            if owner not in contact_map:
                contact_map[owner] = set()
            contact_map[owner].add(registered)
        
        owner_contacts = contact_map.get(owner_id, set())
        
        # Update mutual friends count
        for match in matches:
            user_id = int(match.user_id)
            user_contacts = contact_map.get(user_id, set())
            match.mutual_friends = len(owner_contacts & user_contacts)
        
        return matches

    async def sync_contacts(
        self,
        db: Session,
        owner_id: int,
        contacts: List[ContactInfo]
    ) -> List[UserMatchInfo]:
        """Optimized contact sync with batch processing"""
        try:
            # Build phone index once (not for each contact!)
            phone_to_user = self._build_phone_index(db)
            
            matches = []
            
            # Process contacts in chunks
            for i in range(0, len(contacts), self.chunk_size):
                chunk = contacts[i:i + self.chunk_size]
                chunk_matches = await self._process_contact_chunk(
                    db, owner_id, chunk, phone_to_user
                )
                matches.extend(chunk_matches)
            
            return matches
            
        except Exception as e:
            raise ValueError(f"Contact sync failed: {str(e)}")

