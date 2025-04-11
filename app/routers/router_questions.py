from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.schemas.schema_question import QuestionCreate, QuestionRead, QuestionUpdate
from app.dependencies import get_current_account, get_session, get_current_manager
from app.models.model_tables import Account, Manager, Question
from app.crud.crud_questions import create_question, read_questions, read_question_by_id, update_question, delete_question
from typing import List, Annotated
from jsonschema import validate, ValidationError
import json
import os

# Load all JSON schemas for questions
schemas_dir = "json_schema/questions"
schemas = {}
for schema_file in os.listdir(schemas_dir):
    if schema_file.endswith(".json"):
        schema_name = schema_file.split(".")[0]
        with open(os.path.join(schemas_dir, schema_file), "r") as file:
            schemas[schema_name] = json.load(file)

router = APIRouter()

@router.post("/{manager_id}", response_model=QuestionRead)
def create_question_route(current_account: Annotated[Account, Depends(get_current_account)], manager: Annotated[Manager, Depends(get_current_manager)], question: QuestionCreate, session: Annotated[Session, Depends(get_session)]) -> QuestionRead:
    schema = schemas.get(question.type)
    if not schema:
        raise HTTPException(status_code=400, detail=f"Unsupported question type: {question.type}")

    try:
        validate(instance=question.exercise, schema=schema)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid exercise format for type '{question.type}': {e.message}")

    question_to_create = Question(**question.model_dump())
    question_to_create.created_by = manager.id
    question_to_create.edited_by = manager.id
    return create_question(session, question_to_create, current_account, manager.id)

@router.get("/", response_model=List[QuestionRead])
def read_questions_route(current_account: Annotated[Account, Depends(get_current_account)], session: Session = Depends(get_session)) -> List[QuestionRead]:
    return read_questions(session, current_account)

@router.get("/{question_id}", response_model=QuestionRead)
def read_question_by_id_route(current_account: Annotated[Account, Depends(get_current_account)], question_id: int, session: Session = Depends(get_session)) -> QuestionRead:
    return read_question_by_id(session, question_id, current_account)

@router.put("/{question_id}", response_model=QuestionRead)
def update_question_route(current_account: Annotated[Account, Depends(get_current_account)], manager_id: int, question_id: int, question: QuestionUpdate, session: Session = Depends(get_session)) -> QuestionRead:
    question_data = Question(**question.model_dump())
    return update_question(session, question_id, question_data, current_account, manager_id)

@router.delete("/{question_id}", response_model=dict)
def delete_question_route(current_account: Annotated[Account, Depends(get_current_account)], question_id: int, session: Session = Depends(get_session)) -> dict:
    delete_question(session, question_id, current_account)
    return {"detail": "Question deleted successfully"}