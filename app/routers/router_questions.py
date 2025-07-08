from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request, Form, BackgroundTasks, Query
from sqlmodel import Session
from app.schemas.schema_question import QuestionCreate, QuestionRead, QuestionUpdate, Clues, PaginatedQuestionsResponse, RawDataRead
from app.dependencies import get_current_account, get_session, get_current_manager, get_validated_question, get_current_question, get_clues_llm, get_embedding_llm, get_current_raw_data
from app.models.model_tables import Account, Manager, Question, RawData
from app.crud.crud_questions import create_question, read_questions, update_question, delete_question, get_nearest_questions, create_raw_data, get_raw_data, get_raw_data_cluster
from typing import List, Annotated, Optional, Union
from jsonschema import validate, ValidationError
from fastapi.responses import FileResponse
import os
import json
from pydantic import ValidationError as PydanticValidationError
from app.llm import LLMModel

QUESTION_IMAGES_ROOT = "media/question_images"
RAW_DATA_ROOT = "media/raw_data"

router = APIRouter()

def get_image_url(request: Request, question: Question):
    if question.image_path:
        return str(request.base_url) + f"api/questions/{question.id}/image"
    return None

def get_file_url(request: Request, raw_data: RawData):
    if raw_data.file_path:
        return str(request.base_url) + f"api/questions/data/{raw_data.id}/file"
    return None

@router.post("/", response_model=QuestionRead)
def create_question_route(question: Annotated[str, Form(...)], current_manager: Annotated[Manager, Depends(get_current_manager)], embedding_model: Annotated[LLMModel, Depends(get_embedding_llm)], session: Annotated[Session, Depends(get_session)], background_tasks: BackgroundTasks, image: UploadFile = File(None)) -> QuestionRead:
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
        os.makedirs(QUESTION_IMAGES_ROOT, exist_ok=True)
        filename = f"question_{current_manager.id}_{image.filename}"
        file_path = os.path.join(QUESTION_IMAGES_ROOT, filename)
        with open(file_path, "wb") as f:
            f.write(image.file.read())
        question_data["image_path"] = file_path
    question_to_create = Question(**question_data)
    return create_question(session, question_to_create, current_manager=current_manager, embedding_model=embedding_model, background_tasks=background_tasks)

@router.get("/", response_model=Union[List[QuestionRead], QuestionRead, PaginatedQuestionsResponse], description="Returns all questions (with optional pagination) or a specific question if question_id query parameter is provided.")
def read_questions_route(
    question: Annotated[Question, Depends(get_current_question)], 
    current_account: Annotated[Account, Depends(get_current_account)], 
    session: Session = Depends(get_session), 
    request: Request = None,
    page: Optional[int] = Query(None, ge=1, description="Page number (starts at 1)"),
    size: Optional[int] = Query(None, ge=1, le=100, description="Items per page (max 100)")
) -> Union[List[QuestionRead], QuestionRead, PaginatedQuestionsResponse]:
    # Si un question_id est fourni, retourner la question spécifique
    if question:
        return QuestionRead(**question.model_dump(), image_url=get_image_url(request, question))
    
    # Sinon, récupérer les questions avec pagination optionnelle
    base_url = str(request.base_url) if request else ""
    result = read_questions(session, current_account, base_url, page, size)
    
    # Si pagination demandée, retourner une réponse paginée
    if page is not None and size is not None:
        questions, meta = result        
        return PaginatedQuestionsResponse(items=questions, meta=meta)
    
    # Sinon, comportement original pour la compatibilité
    return result

@router.put("/", response_model=QuestionRead)
def update_question_route(question: Annotated[str, Form(...)], current_question: Annotated[Question, Depends(get_current_question)], current_manager: Annotated[Manager, Depends(get_current_manager)], embedding_model: Annotated[LLMModel, Depends(get_embedding_llm)], session: Annotated[Session, Depends(get_session)], background_tasks: BackgroundTasks) -> QuestionRead:
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
    return update_question(session, question_data, current_question, current_manager, embedding_model, background_tasks)

@router.delete("/", response_model=dict)
def delete_question_route(current_question: Annotated[Question, Depends(get_current_question)], session: Annotated[Session, Depends(get_session)]) -> dict:
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

@router.get("/{question_id}/clues", response_model=Clues)
async def get_clues_route(current_question: Annotated[Question, Depends(get_current_question)], clues_llm: Annotated[LLMModel, Depends(get_clues_llm)], embedding_model: Annotated[LLMModel, Depends(get_embedding_llm)], session: Annotated[Session, Depends(get_session)]) -> Clues:
    if clues_llm is None or embedding_model is None:
        raise HTTPException(status_code=503, detail="LLM service is not activated")
    
    nearest_questions = get_nearest_questions(session, current_question)

    prompt = f"{current_question.exercise}\n\n"
    if nearest_questions:
        prompt += f"context: {nearest_questions}\n\n"
    prompt += "Vérifie bien que la réponse N'EST PAS dans les indices que tu donnes."

    return await clues_llm.generate(current_question.exercise, format=Clues)

@router.post("/data", response_model=RawDataRead)
def import_data_route(
    text: Annotated[str, Form(...)], 
    current_account: Annotated[Account, Depends(get_current_account)], 
    current_manager: Annotated[Manager, Depends(get_current_manager)],
    session: Annotated[Session, Depends(get_session)], 
    background_tasks: BackgroundTasks,
    file: UploadFile = File(None),
    request: Request = None
) -> RawDataRead:
    file_path = None
    if file:
        os.makedirs(RAW_DATA_ROOT, exist_ok=True)
        file_path = os.path.join(RAW_DATA_ROOT, f"raw_data")

    raw_data = create_raw_data(
        session=session,
        text=text,
        current_account=current_account,
        current_manager=current_manager,
        file_path=file_path,
        filename=file.filename if file else None,
        embedding_model=get_embedding_llm(),
        background_tasks=background_tasks
    )

    if file:
        file_path=raw_data.file_path
        with open(file_path, "wb") as f:
            f.write(file.file.read())

    return RawDataRead(
        id=raw_data.id,
        text=raw_data.text,
        created_at=raw_data.created_at,
        updated_at=raw_data.updated_at,
        created_by=raw_data.created_by,
        edited_by=raw_data.edited_by,
        image_url=get_file_url(request, raw_data)
    )

@router.get("/data", response_model=list[RawDataRead])
def get_raw_data_route(
    current_account: Annotated[Account, Depends(get_current_account)],
    session: Annotated[Session, Depends(get_session)],
    request: Request = None
) -> list[RawDataRead]:
    raw_data_list = get_raw_data(session, current_account)
    if raw_data_list is None:
        return []
    raw_data_read_list = []
    for raw_data in raw_data_list:
        raw_data_read_list.append(RawDataRead(
            id=raw_data.id,
            text=raw_data.text,
            created_at=raw_data.created_at,
            updated_at=raw_data.updated_at,
            created_by=raw_data.created_by,
            edited_by=raw_data.edited_by,
            image_url=get_file_url(request, raw_data)
        ))
    return raw_data_read_list

@router.get("/data/{raw_data_id}/file")
def get_raw_data_file_route(
    raw_data: Annotated[RawData, Depends(get_current_raw_data)]
) -> FileResponse:
    if not raw_data.file_path or not os.path.exists(raw_data.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(raw_data.file_path)