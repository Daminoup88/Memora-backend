from sqlmodel import Session, select, func
from fastapi import HTTPException, BackgroundTasks
from app.models.model_tables import Question, Account, Manager
from app.llm import LLMModel
from app.config import logger
from app.schemas.schema_pagination import PaginationMeta
from app.schemas.schema_question import QuestionRead
from app.dependencies import get_image_url
from typing import Optional
import math

def _question_to_read(question: Question, base_url: str) -> QuestionRead:
    return QuestionRead(**question.model_dump(), image_url=get_image_url(base_url, question))

async def calculate_embedding_in_background(question: Question, session: Session, embedding_model: LLMModel):
    question.embedding = await embedding_model.embed(str(question.exercise))
    session.commit()
    logger.debug(f"Embedding calculated in background for question ID {question.id}")

async def create_question(session: Session, question: Question, current_manager: Manager, embedding_model: LLMModel, background_tasks: BackgroundTasks) -> Question:
    question.created_by = current_manager.id
    question.edited_by = current_manager.id
    question.account_id = current_manager.account_id
    session.add(question)
    session.commit()
    session.refresh(question)

    if embedding_model is not None:
        background_tasks.add_task(calculate_embedding_in_background, question, session, embedding_model)

    return question

def read_questions(session: Session, current_account: Account, base_url: str, page: Optional[int] = None, size: Optional[int] = None) -> list[QuestionRead] | tuple[list[QuestionRead], PaginationMeta]:
    base_query = select(Question).join(Account).where(Question.account_id == current_account.id)
    
    # Si pas de pagination demandée, comportement original
    if page is None or size is None:
        questions = session.exec(base_query).all()
        return [_question_to_read(question, base_url) for question in questions]
    
    # Calcul du total et pagination (validations déjà faites dans le router)
    total = session.exec(select(func.count(Question.id)).join(Account).where(Question.account_id == current_account.id)).first()
    pages = math.ceil(total / size) if total > 0 else 1
    
    # Ajustement de la page si trop élevée
    page = min(page, pages)
    
    # Requête paginée
    offset = (page - 1) * size
    questions = session.exec(base_query.offset(offset).limit(size)).all()
    
    return [_question_to_read(question, base_url) for question in questions], PaginationMeta(
        page=page, size=size, total=total, pages=pages
    )

async def update_question(session: Session, question_data: Question, current_question: Question, current_manager: Manager, embedding_model: LLMModel, background_tasks: BackgroundTasks) -> Question:
    question_data.edited_by = current_manager.id

    for key, value in question_data.model_dump().items():
        if value is not None:
            setattr(current_question, key, value)
    
    if embedding_model is not None:
        background_tasks.add_task(calculate_embedding_in_background, current_question, session, embedding_model)
    return current_question

def delete_question(session: Session, current_question: Question) -> bool:
    session.delete(current_question)
    session.commit()
    return True

def get_nearest_questions(session: Session, current_question: Question, limit: int = 5) -> list[Question]:
    if current_question.embedding is None:
        raise HTTPException(status_code=400, detail="Question does not have an embedding")

    nearest_questions = session.exec(
        select(Question.exercise)
        .where(Question.account_id == current_question.account_id, Question.id != current_question.id)
        .order_by(Question.embedding.l2_distance(current_question.embedding))
        .limit(limit)
    ).all()

    return nearest_questions