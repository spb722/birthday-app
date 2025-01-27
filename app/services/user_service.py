from sqlalchemy.orm import Session
from typing import Optional
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ..core.security import get_password_hash,verify_password

class UserService:
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        db_user = User(
            email=user_in.email,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            hashed_password=get_password_hash(user_in.password) if user_in.password else None
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
        update_data = user_in.dict(exclude_unset=True)

        # Handle password hashing if provided
        if 'password' in update_data:
            update_data['hashed_password'] = get_password_hash(update_data.pop('password'))

        for field, value in update_data.items():
            setattr(user, field, value)

        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    @staticmethod
    def authenticate_phone(db: Session, phone: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.phone == phone).first()
        if not user or not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

