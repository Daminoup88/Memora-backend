from typing import Annotated
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
from app.dependencies import get_session, get_current_account
from app.models.model_tables import Account
from app.schemas.schema_statistics import StatisticsRead, RegularityStats
from app.crud.crud_statistics import calculate_statistics, calculate_regularity_statistics

router = APIRouter()

@router.get("/", response_model=StatisticsRead)
def get_statistics(
    current_account: Annotated[Account, Depends(get_current_account)], 
    session: Session = Depends(get_session),
    request: Request = None
) -> StatisticsRead:
    stats = calculate_statistics(session, current_account, request)
    return StatisticsRead(**stats)

@router.get("/regularity", response_model=RegularityStats)
def get_regularity_statistics(
    current_account: Annotated[Account, Depends(get_current_account)], 
    session: Session = Depends(get_session)
) -> RegularityStats:
    stats = calculate_regularity_statistics(session, current_account)
    return RegularityStats(**stats)
