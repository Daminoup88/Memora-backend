from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request, Form
from sqlmodel import Session
from app.schemas.schema_question import QuestionCreate, QuestionRead, QuestionUpdate
from app.dependencies import get_current_account, get_session, get_current_manager, get_validated_question, get_current_question
from app.models.model_tables import Account, Manager, Question
from app.crud.crud_questions import create_question, read_questions, update_question, delete_question
from typing import List, Annotated
from jsonschema import validate, ValidationError
from fastapi.responses import FileResponse
import os
import json
from pydantic import ValidationError as PydanticValidationError

MEDIA_ROOT = "media/question_images"

router = APIRouter()

def get_image_url(request: Request, question):
    if question.image_path:
        return str(request.base_url) + f"api/questions/{question.id}/image"
    return None

@router.post("/", response_model=QuestionRead)
def create_question_route(question: Annotated[str, Form(...)], current_manager: Annotated[Manager, Depends(get_current_manager)], session: Annotated[Session, Depends(get_session)], image: UploadFile = File(None)) -> QuestionRead:
    try:
        question_dict = json.loads(question)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON for question")
    try:
        question_obj = QuestionCreate(**question_dict)
    except PydanticValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    validated_question = get_validated_question(question_obj)
    question_data = validated_question.model_dump()
    if image:
        allowed_exts = {".png", ".jpeg", ".jpg"}
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in allowed_exts:
            raise HTTPException(status_code=400, detail="Only .png, .jpeg, .jpg files are allowed")
        os.makedirs(MEDIA_ROOT, exist_ok=True)
        filename = f"question_{current_manager.id}_{image.filename}"
        file_path = os.path.join(MEDIA_ROOT, filename)
        with open(file_path, "wb") as f:
            f.write(image.file.read())
        question_data["image_path"] = file_path
    question_to_create = Question(**question_data)
    return create_question(session, question_to_create, current_manager)

@router.get("/", response_model=List[QuestionRead] | QuestionRead, description="Returns all questions or a specific question if question_id query parameter is provided.")
def read_questions_route(question: Annotated[Question, Depends(get_current_question)], current_account: Annotated[Account, Depends(get_current_account)], session: Session = Depends(get_session), request: Request = None) -> List[QuestionRead] | QuestionRead:
    if question:
        data = question.model_dump()
        data["image_url"] = get_image_url(request, question)
        return data
    questions = read_questions(session, current_account)
    result = []
    for q in questions:
        data = q.model_dump()
        data["image_url"] = get_image_url(request, q)
        result.append(data)
    return result

@router.put("/", response_model=QuestionRead)
def update_question_route(
    question: Annotated[str, Form(...)],
    current_question: Annotated[Question, Depends(get_current_question)],
    current_manager: Annotated[Manager, Depends(get_current_manager)],
    session: Session = Depends(get_session)
) -> QuestionRead:
    if not current_question:
        raise HTTPException(status_code=400, detail="question_id query parameter required")
    try:
        question_dict = json.loads(question)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON for question")
    try:
        question_obj = QuestionUpdate(**question_dict)
    except PydanticValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    validated_question = get_validated_question(question_obj)
    question_data = Question(**validated_question.model_dump())
    return update_question(session, question_data, current_question, current_manager)

@router.delete("/", response_model=dict)
def delete_question_route(current_question: Annotated[Question, Depends(get_current_question)], session: Session = Depends(get_session)) -> dict:
    if not current_question:
        raise HTTPException(status_code=400, detail="question_id query parameter required")
    if current_question.image_path and os.path.exists(current_question.image_path):
        os.remove(current_question.image_path)
    delete_question(session, current_question)
    return {"detail": "Question deleted successfully"}

@router.get("/{question_id}/image")
def get_question_image(current_question: Annotated[Question, Depends(get_current_question)]):
    if not current_question.image_path or not os.path.exists(current_question.image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(current_question.image_path)