from sqlmodel import Session, select
from fastapi import HTTPException
from app.models.model_tables import Account, Patient

def create_account(session: Session, account: Account) -> Account:
    account = Account(**account.model_dump())
    
    existing_account = session.exec(select(Account).where(Account.username == account.username)).first()
    if existing_account:
        raise HTTPException(status_code=400, detail="Username already registered")

    session.add(account)
    session.commit()
    session.refresh(account)
    return account

def read_account_by_id(session: Session, account_id: int) -> Account:
    return session.get(Account, account_id)

def read_account_by_username(session: Session, username: str) -> Account:
    return session.exec(select(Account).where(Account.username == username)).first()

def update_account(session: Session, current_account: Account, account: Account) -> Account:
    existing_account = session.exec(select(Account).where(Account.username == account.username)).first()
    if existing_account and existing_account.id != current_account.id:
        raise HTTPException(status_code=400, detail="Username already registered")
    if current_account:
        for key, value in account.model_dump().items():
            if value != None:
                setattr(current_account, key, value)
        session.commit()
        session.refresh(current_account)
        return current_account
    return None # pragma: no cover (security measure)

def delete_account(session: Session, current_account: Account) -> bool:
    if current_account.patient_id:
        patient = session.get(Patient, current_account.patient_id)
        if patient:
            session.delete(patient)
            session.commit()
    if current_account:
        session.delete(current_account)
        session.commit()
        return True
    return False # pragma: no cover (security measure)