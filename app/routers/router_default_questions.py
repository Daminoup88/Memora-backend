from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.dependencies import get_session
from app.models.model_tables import DefaultQuestions
from typing import List

router = APIRouter()

@router.get("/", response_model=List[DefaultQuestions])
def get_default_questions(session: Session = Depends(get_session)) -> List[DefaultQuestions]:
    return session.exec(select(DefaultQuestions)).all()
