from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlmodel import Session
from app.models.model_tables import Account, Manager
from app.schemas.schema_manager import ManagerRead, ManagerCreate, ManagerUpdate
from app.dependencies import get_session, get_current_account, get_current_manager
from app.crud.crud_manager import create_manager, update_manager, delete_manager, read_managers
from typing import Annotated
from fastapi.responses import FileResponse
import os

MEDIA_ROOT = "media/pp"

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

@router.post("/{manager_id}/upload_pp", response_model=dict)
def upload_profile_picture(
    current_manager: Annotated[Manager, Depends(get_current_manager)],
    session: Annotated[Session, Depends(get_session)],
    file: UploadFile = File(...)
):
    allowed_exts = {".png", ".jpeg", ".jpg"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Only .png, .jpeg, .jpg files are allowed")
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    filename = f"manager_{current_manager.id}{ext}"
    file_path = os.path.join(MEDIA_ROOT, filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    current_manager.pp_path = file_path
    session.add(current_manager)
    session.commit()
    return {"detail": "Profile picture uploaded", "pp_path": file_path}

@router.get("/{manager_id}/profile_picture")
def get_profile_picture(current_manager: Annotated[Manager, Depends(get_current_manager)]):
    if not current_manager.pp_path or not os.path.exists(current_manager.pp_path):
        raise HTTPException(status_code=404, detail="Profile picture not found")
    return FileResponse(current_manager.pp_path)