from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.models.model_user import User
from app.schemas.schema_user import UserCreate, UserRead
from app.dependencies import get_session, get_password_hash, get_current_user
from app.crud.crud_user import create_user, read_user_by_id, update_user, delete_user
from typing import Annotated

router = APIRouter(responses={400: {"description": "Bad Request", "content": {"application/json": {"example": {"detail": "string"}}}},
                              401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "string"}}}},
                              404: {"description": "Not found", "content": {"application/json": {"example": {"detail": "string"}}}},
                              422: {"description": "Unprocessable Entity", "content": {"application/json": {"example": {"detail": "string"}}}}
                              })

@router.post("/", response_model=UserRead)
def create_user_route(user: UserCreate, session: Session = Depends(get_session)) -> UserRead:
    user_to_create = User(**user.model_dump())
    user_to_create.hashed_password = get_password_hash(user.password)
    return create_user(session, user_to_create)

@router.get("/", response_model=UserRead)
def read_user_route(current_user: Annotated[User, Depends(get_current_user)], session: Session = Depends(get_session)) -> UserRead:
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found") # pragma: no cover (security measure)
    return read_user_by_id(session, current_user.id)

@router.put("/", response_model=UserRead)
def update_user_route(current_user: Annotated[User, Depends(get_current_user)], user: UserCreate, session: Session = Depends(get_session)) -> UserRead:
    user_to_update = User(**user.model_dump())
    user_to_update.hashed_password = get_password_hash(user.password)
    updated_user = update_user(session, current_user, user_to_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found") # pragma: no cover (security measure)
    return updated_user

@router.delete("/", response_model=dict)
def delete_user_route(current_user: Annotated[User, Depends(get_current_user)], session: Session = Depends(get_session)) -> dict:
    if not delete_user(session, current_user):
        raise HTTPException(status_code=404, detail="User not found") # pragma: no cover (security measure)
    return {"detail": "User deleted successfully"}