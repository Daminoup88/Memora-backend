from app.schemas.schema_quiz import QuizRead, ResultRead
from sqlmodel import Session
from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_current_account, get_session, get_current_manager, get_validated_question, get_current_question, get_current_quiz, get_validated_answer
from app.models.model_tables import Account, Manager, Question, Quiz, QuizQuestion, Result
from typing import List, Annotated
from app.crud.crud_quiz import create_leitner_quiz, have_all_questions_been_answered, save_answer
from app.schemas.schema_quiz import ResultRead

router = APIRouter()

@router.get("/{number_of_questions}", response_model=QuizRead, description="Creates and returns a quiz with a specified number of questions. If all questions from previous quizzes have not been answered, an error is raised.")
def create_and_read_quiz_route(number_of_questions: int, current_account: Annotated[Session, Depends(get_current_account)], session: Annotated[Session, Depends(get_session)]) -> QuizRead:
    if not have_all_questions_been_answered(current_account, session):
        raise HTTPException(status_code=400, detail="All questions from previous quizzes have not been answered yet")
    return create_leitner_quiz(number_of_questions, current_account)

@router.get("/{quiz_id}", response_model=QuizRead)
def read_quiz_by_id_route(current_quiz: Annotated[Quiz, Depends(get_current_quiz)], current_account: Annotated[Session, Depends(get_current_account)], session: Annotated[Session, Depends(get_session)]) -> QuizRead:
    pass

@router.post("/", response_model=ResultRead)
def answer_question_route(answer: Annotated[Result, Depends(get_validated_answer)], current_quiz: Annotated[Quiz, Depends(get_current_quiz)], current_question: Annotated[Question, Depends(get_current_question)], session: Annotated[Session, Depends(get_session)]) -> ResultRead:
    if not current_question:
        raise HTTPException(status_code=400, detail="question_id query parameter required")

    return save_answer(answer, current_quiz, current_question, session)