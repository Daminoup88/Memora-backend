from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from datetime import timedelta
from app.models.model_user import User
from app.dependencies import get_session
from app.schemas.schema_token import Token
from app.dependencies import authenticate_user, create_access_token
from typing import Annotated

router = APIRouter(responses={401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "string"}}}},
                              422: {"description": "Unprocessable Entity", "content": {"application/json": {"example": {"detail": "string"}}}}
                              })

@router.post("/token")
def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: Session = Depends(get_session))-> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token, token_type="bearer")