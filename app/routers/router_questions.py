from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.schemas.schema_question import QuestionCreate, QuestionRead, QuestionUpdate
from app.dependencies import get_current_account, get_session, get_current_manager, get_validated_question, get_current_question
from app.models.model_tables import Account, Manager, Question
from app.crud.crud_questions import create_question, read_questions, update_question, delete_question
from typing import List, Annotated
from jsonschema import validate, ValidationError

router = APIRouter()

@router.post("/", response_model=QuestionRead)
def create_question_route(question: Annotated[QuestionCreate, Depends(get_validated_question)], current_manager: Annotated[Manager, Depends(get_current_manager)], session: Annotated[Session, Depends(get_session)]) -> QuestionRead:
    question_to_create = Question(**question.model_dump())
    return create_question(session, question_to_create, current_manager)

@router.get("/", response_model=List[QuestionRead])
def read_questions_route(current_account: Annotated[Account, Depends(get_current_account)], session: Session = Depends(get_session)) -> List[QuestionRead]:
    return read_questions(session, current_account)

@router.get("/", response_model=QuestionRead)
def read_question_by_id_route(question: Annotated[Question, Depends(get_current_question)]) -> QuestionRead:
    return QuestionRead(**question.model_dump())

@router.put("/", response_model=QuestionRead)
def update_question_route(question: Annotated[QuestionUpdate, Depends(get_validated_question)], current_question: Annotated[Question, Depends(get_current_question)], current_manager: Annotated[Manager, Depends(get_current_manager)], session: Session = Depends(get_session)) -> QuestionRead:
    question_data = Question(**question.model_dump())
    return update_question(session, question_data, current_question, current_manager)

@router.delete("/", response_model=dict)
def delete_question_route(current_question: Annotated[Question, Depends(get_current_question)], current_account: Annotated[Account, Depends(get_current_account)], session: Session = Depends(get_session)) -> dict:
    delete_question(session, current_question)
    return {"detail": "Question deleted successfully"}