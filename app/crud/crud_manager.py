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

def read_managers(session: Session, current_account: Account) -> list[Manager]:
    return session.exec(select(Manager).where(Manager.account_id == current_account.id)).all()

def read_manager_by_id(session: Session, manager_id: int, current_account: Account) -> Manager:
    manager = session.get(Manager, manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    if manager.account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")
    return manager

def update_manager(session: Session, manager_id: int, manager_data: Manager, current_account: Account) -> Manager:
    manager = session.get(Manager, manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    if manager.account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")
    
    email_check = session.exec(select(Manager).where(Manager.email == manager_data.email, Manager.id != manager_id)).first()
    if email_check:
        raise HTTPException(status_code=400, detail="Email already used")

    for key, value in manager_data.model_dump().items():
        if value is not None:
            setattr(manager, key, value)

    session.commit()
    session.refresh(manager)
    return manager

def delete_manager(session: Session, manager_id: int, current_account: Account) -> bool:
    manager = session.get(Manager, manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    if manager.account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")

    session.delete(manager)
    session.commit()

    return True
