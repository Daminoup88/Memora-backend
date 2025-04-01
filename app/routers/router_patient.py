from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.models.model_tables import Account, Patient
from app.schemas.schema_patient import PatientSchema
from app.dependencies import get_session, get_current_account
from app.crud.crud_patient import create_patient, read_patient_by_id, update_patient, delete_patient
from typing import Annotated

router = APIRouter(responses={400: {"description": "Bad Request", "content": {"application/json": {"example": {"detail": "string"}}}},
                              401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "string"}}}},
                              404: {"description": "Not found", "content": {"application/json": {"example": {"detail": "string"}}}},
                              422: {"description": "Unprocessable Entity", "content": {"application/json": {"example": {"detail": "string"}}}}
                              })

@router.post("/", response_model=dict)
def create_patient_route(current_account: Annotated[Account, Depends(get_current_account)], patient: PatientSchema, session: Annotated[Session, Depends(get_session)]) -> dict:
    patient_to_create = Patient(**patient.model_dump())
    is_patient_created = create_patient(session, patient_to_create, current_account)
    if is_patient_created:
        return {}
    else:
        raise HTTPException(status_code=500, detail="Creation failed on database") # pragma: no cover (security measure) 

@router.get("/", response_model=Patient)
def read_patient_route(
    current_account: Annotated[Account, Depends(get_current_account)],
    session: Annotated[Session, Depends(get_session)]
) -> Patient:
    if not current_account or current_account.patient_id is None:
        raise HTTPException(status_code=404, detail="Patient not found")  # pragma: no cover (security measure)
    return read_patient_by_id(session, current_account.patient_id)

@router.put("/", response_model=Patient)
def update_patient_route(
    current_account: Annotated[Account, Depends(get_current_account)],
    patient: PatientSchema,
    session: Annotated[Session, Depends(get_session)]
) -> Patient:
    if not current_account or current_account.patient_id is None:
        raise HTTPException(status_code=404, detail="Patient not found")  # pragma: no cover (security measure)

    patient_to_update = Patient(**patient.model_dump())
    updated_patient = update_patient(session, current_account.patient_id, patient_to_update)

    if not updated_patient:
        raise HTTPException(status_code=404, detail="Patient not found")  # pragma: no cover (security measure)
    
    return updated_patient

@router.delete("/", response_model=dict)
def delete_patient_route(
    current_account: Annotated[Account, Depends(get_current_account)],
    session: Annotated[Session, Depends(get_session)]
) -> dict:
    if not current_account or current_account.patient_id is None:
        raise HTTPException(status_code=404, detail="Patient not found")  # pragma: no cover (security measure)

    if not delete_patient(session, current_account.patient_id):
        raise HTTPException(status_code=500, detail="Failed to delete patient")  # pragma: no cover (security measure)

    return {"detail": "Patient deleted successfully"}