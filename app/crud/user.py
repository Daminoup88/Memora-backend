from sqlmodel import Session, select
from fastapi import HTTPException
from app.models.user import User
from app.schemas.user import UserCreate

def create_user(session: Session, user: UserCreate) -> User:
    user = User(**user.model_dump())

    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def read_user(session: Session, user_id: int) -> User:
    return session.get(User, user_id)

def update_user(session: Session, user_id: int, user: UserCreate) -> User:
    db_user = session.get(User, user_id)

    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user and existing_user.id != user_id:
        raise HTTPException(status_code=400, detail="Email already registered")

    if db_user:
        for key, value in user.model_dump().items():
            setattr(db_user, key, value)
        session.commit()
        session.refresh(db_user)
        return db_user
    return None

def delete_user(session: Session, user_id: int) -> bool:
    db_user = session.get(User, user_id)
    if db_user:
        session.delete(db_user)
        session.commit()
        return True
    return False