from sqlmodel import Session, select, func
from fastapi import HTTPException, UploadFile
from app.models.model_tables import Account, Manager
from app.schemas.schema_pagination import PaginationMeta
from typing import Optional
import os
import math

def create_manager(session: Session, manager: Manager, current_account: Account) -> Manager:

    # check if the email is already used
    email_check = session.exec(select(Manager).where(Manager.email == manager.email)).first()
    if email_check:
        raise HTTPException(status_code=400, detail="Email already used")

    manager.account_id = current_account.id
    session.add(manager)
    session.commit()
    session.refresh(manager)

    return manager

def read_managers(session: Session, current_account: Account, page: Optional[int] = None, size: Optional[int] = None) -> list[Manager] | tuple[list[Manager], PaginationMeta]:
    base_query = select(Manager).where(Manager.account_id == current_account.id)
    
    # Si pas de pagination demandée, comportement original
    if page is None or size is None:
        return session.exec(base_query).all()
    
    # Calcul du total et pagination (validations déjà faites dans le router)
    total = session.exec(select(func.count(Manager.id)).where(Manager.account_id == current_account.id)).first()
    pages = math.ceil(total / size) if total > 0 else 1
    
    # Ajustement de la page si trop élevée
    page = min(page, pages)
    
    # Requête paginée
    offset = (page - 1) * size
    managers = session.exec(base_query.offset(offset).limit(size)).all()
    
    return managers, PaginationMeta(page=page, size=size, total=total, pages=pages)

def update_manager(session: Session, manager_data: Manager, current_manager: Manager) -> Manager:    
    email_check = session.exec(select(Manager).where(Manager.email == manager_data.email, Manager.id != current_manager.id)).first()
    if email_check:
        raise HTTPException(status_code=400, detail="Email already used")

    for key, value in manager_data.model_dump().items():
        if value is not None:
            setattr(current_manager, key, value)

    session.commit()
    session.refresh(current_manager)
    return current_manager

def delete_manager(session: Session, current_manager: Manager) -> bool:
    current_manager = session.get(Manager, current_manager.id)
    if not current_manager:
        raise HTTPException(status_code=404, detail="Manager not found") # pragma: no cover (security measure)
    if current_manager.pp_path and os.path.exists(current_manager.pp_path):
        os.remove(current_manager.pp_path)
    session.delete(current_manager)
    session.commit()

    return True

def save_manager_profile_picture(session: Session, current_manager: Manager, file: UploadFile, ext: str) -> str:
    MEDIA_ROOT = "media/pp"
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    filename = f"manager_{current_manager.id}{ext}"
    file_path = os.path.join(MEDIA_ROOT, filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    current_manager.pp_path = file_path
    session.add(current_manager)
    session.commit()
    return file_path
