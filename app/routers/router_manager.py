from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.models.model_tables import Account, Manager
from app.schemas.schema_manager import ManagerRead, ManagerCreate, ManagerChange
from app.dependencies import get_session, get_current_account
from app.crud.crud_manager import create_manager, read_manager_by_id, update_manager, delete_manager, read_managers_by_account_id
from typing import Annotated

router = APIRouter(responses={400: {"description": "Bad Request", "content": {"application/json": {"example": {"detail": "string"}}}},
                              401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "string"}}}},
                              404: {"description": "Not found", "content": {"application/json": {"example": {"detail": "string"}}}},
                              422: {"description": "Unprocessable Entity", "content": {"application/json": {"example": {"detail": "string"}}}}
                              })

@router.post("/", response_model=dict)
def create_manager_route(current_account: Annotated[Account, Depends(get_current_account)], manager: ManagerCreate, session: Annotated[Session, Depends(get_session)]) -> dict:
    manager_to_create = Manager(**manager.model_dump())
    is_manager_created = create_manager(session, manager_to_create, current_account)
    if is_manager_created:
        return {}
    else:
        raise HTTPException(status_code=500, detail="Creation failed on database") # pragma: no cover (security measure)

@router.get("/", response_model=list[ManagerRead])
def read_manager_route(
    current_account: Annotated[Account, Depends(get_current_account)],
    session: Annotated[Session, Depends(get_session)]
) -> list[ManagerRead]:
    if not current_account or current_account.id is None:
        raise HTTPException(status_code=404, detail="Manager not found")  # pragma: no cover (security measure)
    managers = read_managers_by_account_id(session, current_account.id)

    # Convert managers to ManagerRead
    managers_read = [ManagerRead(**manager.model_dump()) for manager in managers]
    
    return managers_read

@router.put("/{manager_id}", response_model=ManagerRead)
def update_manager_route(
    manager_id: int,
    current_account: Annotated[Account, Depends(get_current_account)],
    manager: ManagerChange,
    session: Annotated[Session, Depends(get_session)]
) -> ManagerRead:
    if not current_account or current_account.id is None:
        raise HTTPException(status_code=404, detail="Manager not found")  # pragma: no cover (security measure)

    manager_to_update = Manager(**manager.model_dump())
    updated_manager = update_manager(session, manager_id, manager_to_update)

    if not updated_manager:
        raise HTTPException(status_code=404, detail="Manager not found")  # pragma: no cover (security measure)
    
    return updated_manager

@router.delete("/{manager_id}", response_model=dict)
def delete_manager_route(
    manager_id: int,
    current_account: Annotated[Account, Depends(get_current_account)],
    session: Annotated[Session, Depends(get_session)]
) -> dict:
    if not current_account or current_account.id is None:
        raise HTTPException(status_code=404, detail="Manager not found")  # pragma: no cover (security measure)

    if not delete_manager(session, manager_id):
        raise HTTPException(status_code=500, detail="Failed to delete manager")  # pragma: no cover (security measure)

    return {"detail": "Manager deleted successfully"}