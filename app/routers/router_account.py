from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.models.model_tables import Account
from app.schemas.schema_account import AccountRead, AccountCreate
from app.dependencies import get_session, get_password_hash, get_current_account
from app.crud.crud_account import create_account, read_account_by_id, update_account, delete_account
from typing import Annotated

router = APIRouter(responses={400: {"description": "Bad Request", "content": {"application/json": {"example": {"detail": "string"}}}},
                              401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "string"}}}},
                              404: {"description": "Not found", "content": {"application/json": {"example": {"detail": "string"}}}},
                              422: {"description": "Unprocessable Entity", "content": {"application/json": {"example": {"detail": "string"}}}}
                              })

@router.post("/", response_model=AccountRead)
def create_account_route(account: AccountCreate, session: Annotated[Session, Depends(get_session)]) -> AccountRead:
    account_to_create = Account(**account.model_dump())
    account_to_create.password_hash = get_password_hash(account.password)
    return create_account(session, account_to_create)

@router.get("/", response_model=AccountRead)
def read_account_route(current_account: Annotated[Account, Depends(get_current_account)], session: Annotated[Session, Depends(get_session)]) -> AccountRead:
    if not current_account:
        raise HTTPException(status_code=404, detail="Account not found") # pragma: no cover (security measure)
    return read_account_by_id(session, current_account.id)

@router.put("/", response_model=AccountRead)
def update_account_route(current_account: Annotated[Account, Depends(get_current_account)], account: AccountCreate, session: Annotated[Session, Depends(get_session)]) -> AccountRead:
    account_to_update = Account(**account.model_dump())
    account_to_update.password_hash = get_password_hash(account.password)
    updated_account = update_account(session, current_account, account_to_update)
    if not updated_account:
        raise HTTPException(status_code=404, detail="Account not found") # pragma: no cover (security measure)
    return AccountRead(**updated_account.model_dump())

@router.delete("/", response_model=dict)
def delete_account_route(current_account: Annotated[Account, Depends(get_current_account)], session: Annotated[Session, Depends(get_session)]) -> dict:
    if not delete_account(session, current_account):
        raise HTTPException(status_code=404, detail="Account not found") # pragma: no cover (security measure)
    return {"detail": "Account deleted successfully"}