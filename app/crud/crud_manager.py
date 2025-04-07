from sqlmodel import Session, select
from fastapi import HTTPException
from app.models.model_tables import Account, Manager

def create_manager(session: Session, manager: Manager, current_account: Account) -> bool:

    # check if the email is already used
    email_check = session.exec(select(Manager).where(Manager.email == manager.email)).first()
    if email_check:
        raise HTTPException(status_code=400, detail="Email already used")

    manager.account_id = current_account.id
    session.add(manager)
    session.commit()
    session.refresh(manager)

    return True

def read_managers_by_account_id(session: Session, account_id: int) -> list[Manager]:
    managers = session.exec(select(Manager).where(Manager.account_id == account_id)).all()
    if not managers:
        raise HTTPException(status_code=404, detail="No managers found")

    return managers

def read_manager_by_id(session: Session, manager_id: int) -> Manager:
    manager = session.get(Manager, manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    return manager

def update_manager(session: Session, manager_id: int, manager_data: Manager) -> Manager:
    manager = session.get(Manager, manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    email_check = session.exec(select(Manager).where(Manager.email == manager.email)).first()
    if email_check:
        raise HTTPException(status_code=400, detail="Email already used")

    for key, value in manager_data.model_dump().items():
        if value is not None:
            setattr(manager, key, value)

    session.commit()
    session.refresh(manager)
    return manager

def delete_manager(session: Session, manager_id: int) -> bool:
    manager = session.get(Manager, manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")

    session.delete(manager)
    session.commit()

    return True
