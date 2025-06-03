from sqlmodel import Session, select
from fastapi import HTTPException
from app.models.model_tables import Question, Account, Manager
from app.llm import LLMModel

async def create_question(session: Session, question: Question, current_manager: Manager, embedding_model: LLMModel) -> Question:
    question.created_by = current_manager.id
    question.edited_by = current_manager.id
    question.account_id = current_manager.account_id
    session.add(question)
    session.commit()
    session.refresh(question)
    if embedding_model is not None:
        question.embedding = await embedding_model.embed(str(question.exercise))
        session.commit()
        session.refresh(question)
    return question

def read_questions(session: Session, current_account: Account) -> list[Question]:
    questions = session.exec(
        select(Question).join(Account).where(Question.account_id == current_account.id)
    ).all()
    return questions

async def update_question(session: Session, question_data: Question, current_question: Question, current_manager: Manager, embedding_model: LLMModel) -> Question:
    question_data.edited_by = current_manager.id

    for key, value in question_data.model_dump().items():
        if value is not None:
            setattr(current_question, key, value)
    
    if embedding_model is not None:
        embeddings = await embedding_model.embed(str(current_question.exercise))
        current_question.embedding = embeddings[0]
    session.commit()
    session.refresh(current_question)
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