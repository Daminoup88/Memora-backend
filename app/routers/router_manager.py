from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.models.model_tables import Account, Manager
from app.schemas.schema_manager import ManagerRead, ManagerCreate, ManagerUpdate
from app.dependencies import get_session, get_current_account, get_current_manager
from app.crud.crud_manager import create_manager, update_manager, delete_manager, read_managers
from typing import Annotated

router = APIRouter(responses={400: {"description": "Bad Request", "content": {"application/json": {"example": {"detail": "string"}}}},
                              401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "string"}}}},
                              404: {"description": "Not found", "content": {"application/json": {"example": {"detail": "string"}}}},
                              422: {"description": "Unprocessable Entity", "content": {"application/json": {"example": {"detail": "string"}}}}
                              })

@router.post("/", response_model=ManagerRead)
def create_manager_route(manager: ManagerCreate, current_account: Annotated[Account, Depends(get_current_account)], session: Annotated[Session, Depends(get_session)]) -> ManagerRead:
    manager_to_create = Manager(**manager.model_dump())
    created_manager = create_manager(session, manager_to_create, current_account)
    return ManagerRead(**created_manager.model_dump())

@router.get("/", response_model=list[ManagerRead])
def read_managers_route(current_account: Annotated[Account, Depends(get_current_account)], session: Annotated[Session, Depends(get_session)]) -> list[ManagerRead]:
    managers = read_managers(session, current_account)

    managers_read = [ManagerRead(**manager.model_dump()) for manager in managers]
    
    return managers_read

@router.get("/{manager_id}", response_model=ManagerRead)
def read_manager_by_id_route(current_manager: Annotated[Manager, Depends(get_current_manager)]) -> ManagerRead:
    return ManagerRead(**current_manager.model_dump())

@router.put("/{manager_id}", response_model=ManagerRead)
def update_manager_route(manager_change: ManagerUpdate, current_manager: Annotated[Manager, Depends(get_current_manager)], session: Annotated[Session, Depends(get_session)]) -> ManagerRead:
    manager_to_update = Manager(**manager_change.model_dump())
    updated_manager = update_manager(session, manager_to_update, current_manager)

    if not updated_manager:
        raise HTTPException(status_code=404, detail="Manager not found") # pragma: no cover (security measure)
    
    return updated_manager

@router.delete("/{manager_id}", response_model=dict)
def delete_manager_route(current_manager: Annotated[Manager, Depends(get_current_manager)], session: Annotated[Session, Depends(get_session)]) -> dict:
    if not delete_manager(session, current_manager):
        raise HTTPException(status_code=500, detail="Failed to delete manager") # pragma: no cover (security measure)
    return {"detail": "Manager deleted successfully"}