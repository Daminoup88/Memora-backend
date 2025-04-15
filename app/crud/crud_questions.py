from sqlmodel import Session, select
from fastapi import HTTPException
from app.models.model_tables import Question, Account, Manager

def create_question(session: Session, question: Question, current_manager: Manager) -> Question:
    question.created_by = current_manager.id
    question.edited_by = current_manager.id
    question.account_id = current_manager.account_id
    session.add(question)
    session.commit()
    session.refresh(question)
    return question

def read_questions(session: Session, current_account: Account) -> list[Question]:
    questions = session.exec(
        select(Question).join(Account).where(Question.account_id == current_account.id)
    ).all()
    return questions

def update_question(session: Session, question_data: Question, current_question: Question, current_manager: Manager) -> Question:
    question_data.edited_by = current_manager.id

    for key, value in question_data.model_dump().items():
        if value is not None:
            setattr(current_question, key, value)

    session.commit()
    session.refresh(current_question)
    return current_question

def delete_question(session: Session, current_question: Question) -> bool:
    session.delete(current_question)
    session.commit()
    return True