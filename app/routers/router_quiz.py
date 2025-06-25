from app.schemas.schema_quiz import QuizRead, ResultRead
from sqlmodel import Session
from fastapi import APIRouter, HTTPException, Depends, Request
from app.dependencies import get_current_account, get_session, get_current_manager, get_validated_question, get_current_question, get_current_quiz, get_validated_answer
from app.models.model_tables import Account, Manager, Question, Quiz, QuizQuestion, Result
from typing import List, Annotated
from app.crud.crud_quiz import create_leitner_quiz, have_all_questions_been_answered, save_answer, read_quiz_by_id, get_latest_quiz_remaining_questions
from app.schemas.schema_quiz import ResultRead

router = APIRouter()

@router.get("/{number_of_questions}", response_model=QuizRead, description="Creates a Leitner quiz with the specified number of questions. If the previous quiz has not completely been answered, it will be returned instead.")
def read_leitner_quiz_route(number_of_questions: int, current_account: Annotated[Account, Depends(get_current_account)], session: Annotated[Session, Depends(get_session)], request: Request) -> QuizRead:
    base_url = str(request.base_url)
    if not current_account.patient_id:
        raise HTTPException(status_code=400, detail="The current account is not associated with a patient.")
    latest_quiz_remaining_questions = get_latest_quiz_remaining_questions(current_account, session, base_url)
    if latest_quiz_remaining_questions:
        return latest_quiz_remaining_questions
    return create_leitner_quiz(number_of_questions, current_account, session, base_url)

@router.get("/", response_model=QuizRead)
def read_quiz_by_id_route(current_quiz: Annotated[Quiz, Depends(get_current_quiz)], session: Annotated[Session, Depends(get_session)], request: Request) -> QuizRead:
    base_url = str(request.base_url)
    return read_quiz_by_id(current_quiz, session, base_url)

@router.post("/", response_model=ResultRead)
def answer_question_route(answer: Annotated[Result, Depends(get_validated_answer)], current_quiz: Annotated[Quiz, Depends(get_current_quiz)], current_question: Annotated[Question, Depends(get_current_question)], session: Annotated[Session, Depends(get_session)]) -> ResultRead:
    if not current_question:
        raise HTTPException(status_code=400, detail="question_id query parameter required")

    return save_answer(answer, current_quiz, current_question, session)