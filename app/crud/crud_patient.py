from sqlmodel import Session, select
from fastapi import HTTPException
from app.models.model_tables import Account, Patient

def create_patient(session: Session, patient: Patient, current_account: Account) -> bool:
    if current_account.patient_id is not None:
        raise HTTPException(status_code=400, detail="Patient already registered")
    
    session.add(patient)
    session.commit()
    session.refresh(patient)

    current_account.patient_id = patient.id
    session.add(current_account)
    session.commit()
    session.refresh(current_account)

    return True

def read_patient_by_id(session: Session, patient_id: int) -> Patient:
    patient = session.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

def update_patient(session: Session, patient_id: int, patient_data: Patient) -> Patient:
    patient = session.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    for key, value in patient_data.model_dump().items():
        if value is not None:
            setattr(patient, key, value)

    session.commit()
    session.refresh(patient)
    return patient

def delete_patient(session: Session, patient_id: int) -> bool:
    patient = session.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Vérifier si un compte est associé à ce patient
    account = session.exec(select(Account).where(Account.patient_id == patient_id)).first()
    if account:
        account.patient_id = None  # Dissocier le patient du compte
        session.add(account)  # Ajouter la modification à la session

    # Supprimer le patient
    session.delete(patient)
    session.commit()

    return True
