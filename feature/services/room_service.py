from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime
from typing import Optional, Tuple, List, Dict
from ..models.room import Room, RoomStatus, RoomPrivacy, RoomType, RoomParticipant
from ..schemas.room_schema import (
    RoomCreate, RoomUpdate, RoomFilter, RoomStats, PaginatedResponse, ParticipantPaginatedResponse, ParticipantInfo
)
from datetime import date, datetime
from sqlalchemy import and_, or_, func, desc
from app.models.user import User
# Import friend models and constants
from ..models.friend import FriendRequest, FriendRequestStatus

class RoomService:
    @staticmethod
    async def create_room(
            db: Session,
            owner_id: int,
            room_data: RoomCreate
    ) -> Tuple[bool, str, Optional[Room]]:
        """Create a new room with enhanced validation."""
        try:
            # Check for overlapping rooms for the owner
            # Check for overlapping rooms for the same owner AND same celebrant
            overlapping = db.query(Room).filter(
                and_(
                    Room.owner_id == owner_id,
                    Room.celebrant_id == room_data.celebrant_id,  # Add this condition
                    Room.status != RoomStatus.EXPIRED,
                    Room.is_archived == False,
                    or_(
                        and_(
                            Room.activation_time <= room_data.expiration_time,
                            Room.expiration_time >= room_data.activation_time
                        )
                    )
                )
            ).first()

            if overlapping:
                return False, "You already have a room for this celebrant during this time period", None

            # Check if celebrant_id and owner_id are the same
            if room_data.celebrant_id and str(room_data.celebrant_id) == str(owner_id):
                # Check if user already has a room where they are both owner and celebrant
                existing_room = db.query(Room).filter(
                    and_(
                        Room.owner_id == owner_id,
                        Room.celebrant_id == str(owner_id),
                        Room.status != RoomStatus.EXPIRED,
                        Room.is_archived == False
                    )
                ).first()

                if existing_room:
                    return False, "You can only create one room where you are both the owner and celebrant", None

                # Force privacy type to be PUBLIC
                if room_data.privacy_type != RoomPrivacy.PUBLIC:
                    return False, "When creating a room where you are both the owner and celebrant, the room must be public", None

            # If celebrant_id is provided, check if the celebrant exists
            if room_data.celebrant_id:
                celebrant_id_str = str(room_data.celebrant_id)
                celebrant = db.query(User).filter(User.id == int(celebrant_id_str)).first()
                if not celebrant:
                    return False, f"Celebrant with ID {room_data.celebrant_id} not found", None

                # If celebrant exists but no birthday is provided, use the celebrant's birthday
                celebrant_birthday = room_data.celebrant_birthday
                if celebrant_birthday is None and celebrant.date_of_birth:
                    celebrant_birthday = celebrant.date_of_birth
            else:
                celebrant_birthday = room_data.celebrant_birthday

            room = Room(
                owner_id=owner_id,
                room_name=room_data.room_name,
                description=room_data.description,
                room_type=room_data.room_type,
                privacy_type=room_data.privacy_type,
                max_participants=room_data.max_participants,
                auto_approve_participants=room_data.auto_approve_participants,
                status=RoomStatus.PENDING,
                activation_time=room_data.activation_time,
                expiration_time=room_data.expiration_time,
                metadata=room_data.metadata or {},
                celebrant_id=room_data.celebrant_id,
                celebrant_birthday=celebrant_birthday
            )

            db.add(room)
            db.commit()
            db.refresh(room)

            # Add owner as admin participant
            participant = RoomParticipant(
                room_id=room.id,
                user_id=owner_id,
                is_admin=True,
                status="approved",
                last_active_at=datetime.utcnow()
            )
            db.add(participant)
            db.commit()

            return True, "Room created successfully", room

        except Exception as e:
            db.rollback()
            return False, f"Error creating room: {str(e)}", None

    # Add this new method to the RoomService class in room_service.py
    @staticmethod
    async def activate_room(
            db: Session,
            room_id: str,
            user_id: int
    ) -> Tuple[bool, str, Optional[Room]]:
        """Activate a room. Only the room owner can activate their room."""
        try:
            # Get the room
            room = db.query(Room).filter(Room.id == room_id).first()

            if not room:
                return False, "Room not found", None

            # Check if current user is the owner
            if room.owner_id != user_id:
                return False, "Only the room owner can activate this room", None

            # Check if room is already active
            if room.status == RoomStatus.ACTIVE:
                return True, "Room is already active", room

            # Update the room status to active
            room.status = RoomStatus.ACTIVE
            db.commit()
            db.refresh(room)

            return True, "Room activated successfully", room

        except Exception as e:
            db.rollback()
            return False, f"Error activating room: {str(e)}", None

    @staticmethod
    async def get_pending_join_requests(
            db: Session,
            room_id: str,
            owner_id: int,
            page: int = 1,
            page_size: int = 10
    ) -> ParticipantPaginatedResponse:
        """Get users who have requested to join a room (pending status)."""
        try:
            # Verify room exists and user is owner
            room = db.query(Room).filter(Room.id == room_id).first()
            if not room:
                raise ValueError("Room not found")

            if room.owner_id != owner_id:
                raise ValueError("Only room owner can view join requests")

            # Query pending participants
            query = db.query(RoomParticipant).join(
                User, User.id == RoomParticipant.user_id
            ).filter(
                RoomParticipant.room_id == room_id,
                RoomParticipant.status == "pending"
            )

            # Calculate total before pagination
            total = query.count()

            # Apply pagination
            participants = query.order_by(RoomParticipant.joined_at.desc()) \
                .offset((page - 1) * page_size) \
                .limit(page_size) \
                .all()

            # Format response data
            items = []
            for participant in participants:
                participant_info = ParticipantInfo(
                    user_id=participant.user_id,
                    first_name=participant.user.first_name,
                    last_name=participant.user.last_name,
                    profile_picture_url=participant.user.profile_picture_url,
                    joined_at=participant.joined_at,
                    status=participant.status
                )
                items.append(participant_info)

            return ParticipantPaginatedResponse(
                items=items,
                total=total,
                page=page,
                size=page_size,
                pages=(total + page_size - 1) // page_size
            )

        except Exception as e:
            raise ValueError(f"Error getting join requests: {str(e)}")
    @staticmethod
    async def invite_users(
            db: Session,
            room_id: str,
            sender_id: int,
            user_ids: List[int],
            message: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Room]]:
        """Invite users to a room."""
        try:
            # Get the room
            room = db.query(Room).filter(Room.id == room_id).first()

            if not room:
                return False, "Room not found", None

            # Check if sender is an admin in the room
            sender_participant = db.query(RoomParticipant).filter(
                and_(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.user_id == sender_id,
                    RoomParticipant.is_admin == True
                )
            ).first()

            if not sender_participant:
                return False, "Only room admins can send invitations", None

            # Check if room is active
            if not room.is_active():
                return False, "Cannot invite users to inactive room", None

            # Process each user invitation
            success_count = 0
            for user_id in user_ids:
                # Check if user exists
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    continue

                # Check if already a participant
                existing = db.query(RoomParticipant).filter(
                    and_(
                        RoomParticipant.room_id == room_id,
                        RoomParticipant.user_id == user_id
                    )
                ).first()

                if existing:
                    if existing.status == "banned":
                        continue  # Skip banned users
                    if existing.status == "approved" or existing.status == "pending":
                        continue  # Skip users who are already participants or have pending invitations

                # Create new participant with pending status
                participant = RoomParticipant(
                    room_id=room_id,
                    user_id=user_id,
                    is_admin=False,
                    status="pending",
                    last_active_at=datetime.utcnow()
                )
                db.add(participant)
                success_count += 1

            db.commit()
            db.refresh(room)

            return True, f"Successfully invited {success_count} users", room

        except Exception as e:
            db.rollback()
            return False, f"Error inviting users: {str(e)}", None
    @staticmethod
    async def get_pending_invitations(
            db: Session,
            user_id: int,
            page: int = 1,
            page_size: int = 10
    ) -> PaginatedResponse:
        """Get all rooms where the user has a pending invitation."""
        try:
            # Query rooms where the user is a participant with 'pending' status
            query = db.query(Room).join(
                RoomParticipant,
                and_(
                    RoomParticipant.room_id == Room.id,
                    RoomParticipant.user_id == user_id,
                    RoomParticipant.status == "pending"
                )
            )

            # Calculate total before pagination
            total = query.count()

            # Apply pagination and ordering
            query = query.order_by(desc(Room.created_at)) \
                .offset((page - 1) * page_size) \
                .limit(page_size)

            rooms = query.all()

            return PaginatedResponse(
                items=rooms,
                total=total,
                page=page,
                size=page_size,
                pages=(total + page_size - 1) // page_size
            )

        except Exception as e:
            raise ValueError(f"Error getting pending invitations: {str(e)}")

    @staticmethod
    async def list_rooms(
            db: Session,
            user_id: int,
            filter_params: RoomFilter,
            page: int = 1,
            page_size: int = 10
    ) -> PaginatedResponse:
        """List rooms with enhanced filtering and pagination."""
        try:
            query = db.query(Room).outerjoin(RoomParticipant)

            # Base filters
            if not filter_params.is_archived:
                query = query.filter(Room.is_archived == False)

            # Apply my_rooms filter
            if filter_params.my_rooms:
                # Use subquery for better performance
                participant_subquery = db.query(RoomParticipant.room_id).filter(
                    RoomParticipant.user_id == user_id,
                    RoomParticipant.status.in_(["approved", "pending"])
                ).subquery()
                
                query = query.filter(
                    or_(
                        Room.owner_id == user_id,
                        Room.id.in_(participant_subquery)
                    )
                )

            # Apply room type filter
            if filter_params.room_type:
                query = query.filter(Room.room_type.in_(filter_params.room_type))

            # Apply status filter
            if filter_params.status:
                query = query.filter(Room.status.in_(filter_params.status))

            # Apply date range filter
            if filter_params.from_date:
                query = query.filter(Room.activation_time >= filter_params.from_date)
            if filter_params.to_date:
                query = query.filter(Room.expiration_time <= filter_params.to_date)

            # Apply birthday date range filter
            if filter_params.birthday_from_date:
                query = query.filter(Room.celebrant_birthday >= filter_params.birthday_from_date)
            if filter_params.birthday_to_date:
                query = query.filter(Room.celebrant_birthday <= filter_params.birthday_to_date)

            # Apply text search if provided
            if filter_params.query:
                search = f"%{filter_params.query}%"
                query = query.filter(
                    or_(
                        Room.room_name.ilike(search),
                        Room.description.ilike(search)
                    )
                )

            # Filter by owner if specified
            if filter_params.owner_id:
                query = query.filter(Room.owner_id == filter_params.owner_id)

            # Filter by friends only if requested
            if filter_params.friends_only:
                # Import FriendRepository here to avoid circular imports
                from ..repository.friend_repository import FriendRepository

                # Get all accepted friend requests where the user is either the requester or receiver
                friend_requests = db.query(FriendRequest).filter(
                    and_(
                        or_(
                            FriendRequest.requester_id == user_id,
                            FriendRequest.receiver_id == user_id
                        ),
                        FriendRequest.status == FriendRequestStatus.ACCEPTED
                    )
                ).all()

                # Extract friend IDs
                friend_ids = []
                for request in friend_requests:
                    friend_id = request.receiver_id if request.requester_id == user_id else request.requester_id
                    friend_ids.append(friend_id)

                # Add current user's ID to the list to also show their own rooms
                friend_ids.append(user_id)

                # Filter rooms to only show those created by friends
                if friend_ids:
                    query = query.filter(Room.owner_id.in_(friend_ids))
                else:
                    # If user has no friends, only show their own rooms
                    query = query.filter(Room.owner_id == user_id)

            # Add distinct to avoid duplicates when using joins
            if filter_params.my_rooms or filter_params.friends_only:
                query = query.distinct()

            # Calculate total before pagination
            total = query.count()

            # Apply pagination
            query = query.order_by(desc(Room.created_at)) \
                .offset((page - 1) * page_size) \
                .limit(page_size)

            rooms = query.all()

            return PaginatedResponse(
                items=rooms,
                total=total,
                page=page,
                size=page_size,
                pages=(total + page_size - 1) // page_size
            )

        except Exception as e:
            raise ValueError(f"Error listing rooms: {str(e)}")

    @staticmethod
    async def join_room(
            db: Session,
            room_id: str,
            user_id: int
    ) -> Tuple[bool, str, Optional[Room]]:
        """Request to join a room with enhanced validation."""
        try:
            # Get room with details
            room = await RoomService.get_room_by_id(db, room_id)
            if not room:
                return False, "Room not found", None

            # Check if room is active
            if not room.is_active():
                return False, "Room is not active", None

            # Check if room has reached maximum participants
            if room.max_participants:
                participant_count = db.query(RoomParticipant) \
                    .filter(
                    and_(
                        RoomParticipant.room_id == room_id,
                        RoomParticipant.status == "approved"
                    )
                ).count()
                if participant_count >= room.max_participants:
                    return False, "Room has reached maximum participants", None

            # Check if user is already a participant
            existing_participant = db.query(RoomParticipant).filter(
                and_(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.user_id == user_id
                )
            ).first()

            if existing_participant:
                if existing_participant.status == "banned":
                    return False, "You are banned from this room", None
                return False, "Already a participant in this room", room

            # For private rooms, status is pending until approved
            # For public rooms with auto-approve, status is approved
            status = "approved" if (
                    room.privacy_type == RoomPrivacy.PUBLIC and
                    room.auto_approve_participants
            ) else "pending"

            # Create new participant
            participant = RoomParticipant(
                room_id=room_id,
                user_id=user_id,
                is_admin=False,
                status=status,
                last_active_at=datetime.utcnow()
            )
            db.add(participant)
            db.commit()

            # Update room's last activity
            room.last_activity = datetime.utcnow()
            db.commit()
            db.refresh(room)

            success_message = "Successfully joined room" if status == "approved" else \
                "Join request sent successfully"
            return True, success_message, room

        except Exception as e:
            db.rollback()
            return False, f"Error joining room: {str(e)}", None

    @staticmethod
    async def get_room_by_id(
            db: Session,
            room_id: str
    ) -> Optional[Room]:
        """Get room by ID with all relationships loaded."""
        try:
            room = db.query(Room) \
                .filter(Room.id == room_id) \
                .first()

            if room:
                # Get participant count
                participant_count = db.query(RoomParticipant) \
                    .filter(
                    and_(
                        RoomParticipant.room_id == room_id,
                        RoomParticipant.status == "approved"
                    )
                ).count()

                # Update last activity if accessed
                room.last_activity = datetime.utcnow()
                db.commit()

            return room

        except Exception as e:
            db.rollback()
            raise ValueError(f"Error fetching room: {str(e)}")
    @staticmethod
    async def update_participant(
            db: Session,
            room_id: str,
            admin_id: int,
            user_id: int,
            new_status: str
    ) -> Tuple[bool, str, Optional[Room]]:
        """Update individual participant status."""
        try:
            # Verify admin has permission
            admin_participant = db.query(RoomParticipant).filter(
                and_(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.user_id == admin_id,
                    RoomParticipant.is_admin == True
                )
            ).first()

            if not admin_participant:
                return False, "Not authorized to update participants", None

            # Update participant status
            participant = db.query(RoomParticipant).filter(
                and_(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.user_id == user_id
                )
            ).first()

            if not participant:
                return False, "Participant not found", None

            participant.status = new_status
            participant.updated_at = datetime.utcnow()
            db.commit()

            # Get updated room
            room = db.query(Room).filter(Room.id == room_id).first()
            return True, "Participant status updated successfully", room

        except Exception as e:
            db.rollback()
            return False, f"Error updating participant: {str(e)}", None

    @staticmethod
    async def get_room_stats(
            db: Session,
            room_id: str
    ) -> Optional[RoomStats]:
        """Get detailed room statistics."""
        try:
            room = db.query(Room).filter(Room.id == room_id).first()
            if not room:
                return None

            participants = db.query(RoomParticipant) \
                .filter(RoomParticipant.room_id == room_id)

            total_participants = participants.count()
            active_participants = participants.filter(
                RoomParticipant.status == "approved"
            ).count()
            pending_requests = participants.filter(
                RoomParticipant.status == "pending"
            ).count()

            capacity_used = (total_participants / room.max_participants * 100) \
                if room.max_participants else 0

            return RoomStats(
                total_participants=total_participants,
                active_participants=active_participants,
                pending_requests=pending_requests,
                last_activity=room.last_activity,
                capacity_used=capacity_used
            )

        except Exception as e:
            raise ValueError(f"Error getting room stats: {str(e)}")

    @staticmethod
    async def update_room(
            db: Session,
            room_id: str,
            user_id: int,
            update_data: RoomUpdate
    ) -> Tuple[bool, str, Optional[Room]]:
        """Update room settings."""
        try:
            room = db.query(Room).filter(Room.id == room_id).first()
            if not room:
                return False, "Room not found", None

            if room.owner_id != user_id:
                return False, "Not authorized to update this room", None

            update_dict = update_data.dict(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(room, key, value)

            room.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(room)

            return True, "Room updated successfully", room

        except Exception as e:
            db.rollback()
            return False, f"Error updating room: {str(e)}", None

    @staticmethod
    async def bulk_update_participants(
            db: Session,
            room_id: str,
            admin_id: int,
            user_ids: List[int],
            action: str
    ) -> Tuple[bool, str, Dict[str, int]]:
        """Bulk update participant statuses."""
        try:
            # Verify admin has permission
            admin_participant = db.query(RoomParticipant).filter(
                and_(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.user_id == admin_id,
                    RoomParticipant.is_admin == True
                )
            ).first()

            if not admin_participant:
                return False, "Not authorized for bulk updates", None

            # Update participants
            updated = db.query(RoomParticipant).filter(
                and_(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.user_id.in_(user_ids)
                )
            ).update(
                {"status": action, "updated_at": datetime.utcnow()},
                synchronize_session=False
            )

            db.commit()

            return True, f"Updated {updated} participants", {"updated_count": updated}

        except Exception as e:
            db.rollback()
            return False, f"Error in bulk update: {str(e)}", None

    @staticmethod
    async def archive_room(
            db: Session,
            room_id: str,
            user_id: int
    ) -> Tuple[bool, str, Optional[Room]]:
        """Archive a room (soft delete)."""
        try:
            room = db.query(Room).filter(Room.id == room_id).first()
            if not room:
                return False, "Room not found", None

            if room.owner_id != user_id:
                return False, "Not authorized to archive this room", None

            room.is_archived = True
            room.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(room)

            return True, "Room archived successfully", room

        except Exception as e:
            db.rollback()
            return False, f"Error archiving room: {str(e)}", None

    @staticmethod
    async def update_participant_activity(
            db: Session,
            room_id: str,
            user_id: int
    ) -> bool:
        """Update participant's last activity timestamp."""
        try:
            participant = db.query(RoomParticipant).filter(
                and_(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.user_id == user_id
                )
            ).first()

            if participant:
                participant.last_active_at = datetime.utcnow()
                db.commit()
                return True
            return False

        except Exception:
            db.rollback()
            return False