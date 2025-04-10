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
    session.delete(current_manager)
    session.commit()

    return True
