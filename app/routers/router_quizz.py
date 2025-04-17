from app.schemas.schema_quizz import QuizzGet
from sqlmodel import Session
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_current_account, get_session, get_current_manager, get_validated_question, get_current_question
from app.models.model_tables import Account, Manager, Question
from typing import List, Annotated
from app.crud.crud_quizz import algo_box

router = APIRouter()

@router.get("/{length}", response_model=QuizzGet)
def get_quizz_questions(session: Annotated[Session, Depends(get_session)], length: int) -> QuizzGet:
    return algo_box(length)
