from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.dependencies import get_session
from app.crud.user import create_user, read_user, update_user, delete_user

router = APIRouter(responses={404: {"description": "Not found", "content": {"application/json": {"example": {"detail": "string"}}}},
                              400: {"description": "Bad Request", "content": {"application/json": {"example": {"detail": "string"}}}}})

@router.post("/", response_model=UserRead)
def create_user_route(user: UserCreate, session: Session = Depends(get_session)):
    return create_user(session, user)

@router.get("/{user_id}", response_model=UserRead)
def read_user_route(user_id: int, session: Session = Depends(get_session)):
    user = read_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserRead)
def update_user_route(user_id: int, user: UserCreate, session: Session = Depends(get_session)):
    updated_user = update_user(session, user_id, user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/{user_id}", response_model=dict)
def delete_user_route(user_id: int, session: Session = Depends(get_session)):
    if not delete_user(session, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}