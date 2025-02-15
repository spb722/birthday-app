from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Tuple, List
from ..models.room import Room, RoomStatus, RoomPrivacy, RoomParticipant
from app.models.user import User
from sqlalchemy import and_, or_
from ..schemas.room_schema import RoomCreate


class RoomService:
    @staticmethod
    async def get_user_rooms(
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 10
    ) -> List[Room]:
        """Get all rooms owned by a user."""
        return db.query(Room)\
            .filter(Room.owner_id == user_id)\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    async def create_room(
            db: Session,
            owner_id: int,
            room_data: RoomCreate
    ) -> Tuple[bool, str, Optional[Room]]:
        """Create a new room."""
        try:
            room = Room(
                owner_id=owner_id,
                room_name=room_data.room_name,
                privacy_type=room_data.privacy_type,
                status=RoomStatus.PENDING,
                activation_time=room_data.activation_time,
                expiration_time=room_data.expiration_time
            )

            db.add(room)
            db.commit()
            db.refresh(room)

            # Add owner as admin participant
            participant = RoomParticipant(
                room_id=room.id,
                user_id=owner_id,
                is_admin=True,
                status="approved"
            )
            db.add(participant)
            db.commit()

            return True, "Room created successfully", room

        except Exception as e:
            db.rollback()
            return False, f"Error creating room: {str(e)}", None

    @staticmethod
    async def list_rooms(
            db: Session,
            user_id: int,
            room_type: str,
            status: Optional[str] = None,
            skip: int = 0,
            limit: int = 10
    ) -> List[Room]:
        """List rooms based on filters."""
        query = db.query(Room)

        if room_type == "my_rooms":
            # Rooms where user is owner or participant
            query = query.join(RoomParticipant).filter(
                or_(
                    Room.owner_id == user_id,
                    RoomParticipant.user_id == user_id
                )
            )
        elif room_type == "upcoming":
            # Rooms that are:
            # 1. Public rooms
            # 2. Private rooms where user is invited
            # 3. Private rooms where owner is in user's friend list
            from ..models.friend import FriendRequest, FriendRequestStatus

            query = query.outerjoin(RoomParticipant).filter(
                or_(
                    Room.privacy_type == RoomPrivacy.PUBLIC,
                    RoomParticipant.user_id == user_id,
                    and_(
                        Room.privacy_type == RoomPrivacy.PRIVATE,
                        Room.owner_id.in_(
                            db.query(FriendRequest.receiver_id)
                            .filter(
                                and_(
                                    FriendRequest.requester_id == user_id,
                                    FriendRequest.status == FriendRequestStatus.ACCEPTED
                                )
                            )
                            .union(
                                db.query(FriendRequest.requester_id)
                                .filter(
                                    and_(
                                        FriendRequest.receiver_id == user_id,
                                        FriendRequest.status == FriendRequestStatus.ACCEPTED
                                    )
                                )
                            )
                        )
                    )
                )
            )

        if status:
            query = query.filter(Room.status == status)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    async def get_room_by_id(
            db: Session,
            room_id: str
    ) -> Optional[Room]:
        """Get room by ID."""
        return db.query(Room).filter(Room.id == room_id).first()

    @staticmethod
    async def join_room(
            db: Session,
            room_id: str,
            user_id: int
    ) -> Tuple[bool, str, Optional[Room]]:
        """Request to join a room."""
        try:
            room = await RoomService.get_room_by_id(db, room_id)
            if not room:
                return False, "Room not found", None

            # Check if user is already a participant
            existing_participant = db.query(RoomParticipant).filter(
                and_(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.user_id == user_id
                )
            ).first()

            if existing_participant:
                return False, "Already a participant in this room", room

            # For private rooms, status is pending until approved
            status = "approved" if room.privacy_type == RoomPrivacy.PUBLIC else "pending"

            participant = RoomParticipant(
                room_id=room_id,
                user_id=user_id,
                is_admin=False,
                status=status
            )
            db.add(participant)
            db.commit()

            return True, "Successfully joined room", room

        except Exception as e:
            db.rollback()
            return False, f"Error joining room: {str(e)}", None

    @staticmethod
    async def update_participant(
            db: Session,
            room_id: str,
            admin_id: int,
            user_id: int,
            new_status: str
    ) -> Tuple[bool, str, Optional[Room]]:
        """Update participant status."""
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
            db.commit()

            room = await RoomService.get_room_by_id(db, room_id)
            return True, "Participant status updated successfully", room

        except Exception as e:
            db.rollback()
            return False, f"Error updating participant: {str(e)}", None

    @staticmethod
    async def send_invitations(
            db: Session,
            room_id: str,
            sender_id: int,
            user_ids: List[int]
    ) -> Tuple[bool, str, Optional[Room]]:
        """Send room invitations."""
        try:
            room = await RoomService.get_room_by_id(db, room_id)
            if not room:
                return False, "Room not found", None

            # Verify sender has permission
            sender_participant = db.query(RoomParticipant).filter(
                and_(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.user_id == sender_id,
                    RoomParticipant.is_admin == True
                )
            ).first()

            if not sender_participant:
                return False, "Not authorized to send invitations", None

            for user_id in user_ids:
                existing_participant = db.query(RoomParticipant).filter(
                    and_(
                        RoomParticipant.room_id == room_id,
                        RoomParticipant.user_id == user_id
                    )
                ).first()

                if not existing_participant:
                    participant = RoomParticipant(
                        room_id=room_id,
                        user_id=user_id,
                        is_admin=False,
                        status="pending"
                    )
                    db.add(participant)

            db.commit()
            return True, "Invitations sent successfully", room

        except Exception as e:
            db.rollback()
            return False, f"Error sending invitations: {str(e)}", None

    @staticmethod
    async def handle_invitation(
            db: Session,
            room_id: str,
            user_id: int,
            status: str
    ) -> Tuple[bool, str, Optional[Room]]:
        """Handle invitation response."""
        try:
            participant = db.query(RoomParticipant).filter(
                and_(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.user_id == user_id,
                    RoomParticipant.status == "pending"
                )
            ).first()

            if not participant:
                return False, "Invitation not found", None

            participant.status = status
            db.commit()

            room = await RoomService.get_room_by_id(db, room_id)
            return True, f"Invitation {status} successfully", room

        except Exception as e:
            db.rollback()
            return False, f"Error handling invitation: {str(e)}", None

    @staticmethod
    async def delete_room(
            db: Session,
            room_id: str,
            user_id: int
    ) -> Tuple[bool, str]:
        """Delete a room."""
        try:
            room = await RoomService.get_room_by_id(db, room_id)
            if not room:
                return False, "Room not found"

            if room.owner_id != user_id:
                return False, "Not authorized to delete this room"

            db.delete(room)
            db.commit()
            return True, "Room deleted successfully"

        except Exception as e:
            db.rollback()
            return False, f"Error deleting room: {str(e)}"