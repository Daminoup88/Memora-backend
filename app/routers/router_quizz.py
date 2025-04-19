from app.schemas.schema_quizz import QuizzGet, QuizzAnswered
from sqlmodel import Session
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_current_account, get_session, get_current_manager, get_validated_question, get_current_question
from app.models.model_tables import Account, Manager, Question
from typing import List, Annotated
from app.crud.crud_quizz import algo_box, check_answer

router = APIRouter()

@router.get("/", response_model=QuizzGet)
def get_quizz_questions(account: Annotated[Session, Depends(get_current_account)], length: int) -> QuizzGet:
    return algo_box(length)


@router.post("/", response_model=QuizzAnswered)
def get_quizz_questions(
    answer: str,
    quizz_id: int,
    question: Annotated[Question, Depends(get_current_question)],
    session: Annotated[Session, Depends(get_session)]
) -> QuizzAnswered:
    if not quizz_id:
        raise HTTPException(status_code=400, detail="quizz_id query parameter required")
    if not answer:
        raise HTTPException(status_code=400, detail="answer query parameter required")
    if not question:
        raise HTTPException(status_code=400, detail="question_id query parameter required")

    # Vérifie la réponse et retourne le résultat
    is_correct = check_answer(session, question, answer, quizz_id)
    return QuizzAnswered(is_right=is_correct)