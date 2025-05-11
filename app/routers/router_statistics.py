from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.dependencies import get_session, get_current_account
from app.models.model_tables import Account
from app.schemas.schema_statistics import StatisticsRead
from app.crud.crud_statistics import calculate_statistics

router = APIRouter()

@router.get("/", response_model=StatisticsRead)
def get_statistics(
    current_account: Annotated[Account, Depends(get_current_account)], 
    session: Session = Depends(get_session)
) -> StatisticsRead:
    stats = calculate_statistics(session, current_account.id)
    return StatisticsRead(**stats)
