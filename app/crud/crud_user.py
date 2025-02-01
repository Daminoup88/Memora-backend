from sqlmodel import Session, select
from fastapi import HTTPException
from app.models.model_user import User
from app.schemas.schema_user import UserCreate

def create_user(session: Session, user: User) -> User:
    user = User(**user.model_dump())

    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def read_user_by_id(session: Session, user_id: int) -> User:
    return session.get(User, user_id)

def read_user_by_email(session: Session, email: str) -> User:
    return session.exec(select(User).where(User.email == email)).first()

def update_user(session: Session, current_user: User, user: User) -> User:
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(status_code=400, detail="Email already registered")
    if current_user:
        for key, value in user.model_dump().items():
            if value != None:
                setattr(current_user, key, value)
        session.commit()
        session.refresh(current_user)
        return current_user
    return None # pragma: no cover (security measure)

def delete_user(session: Session, current_user: User) -> bool:
    if current_user:
        session.delete(current_user)
        session.commit()
        return True
    return False # pragma: no cover (security measure)