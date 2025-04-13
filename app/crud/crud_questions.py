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

def read_question_by_id(session: Session, question_id: int, current_account: Account) -> Question:
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this question")
    return question

def update_question(session: Session, question_data: Question, current_account: Account, current_manager: Manager) -> Question:
    question = session.get(Question, question_data.id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this question")
    question_data.edited_by = current_manager.id

    for key, value in question_data.model_dump().items():
        if value is not None:
            setattr(question, key, value)

    session.commit()
    session.refresh(question)
    return question

def delete_question(session: Session, question_id: int, current_account: Account) -> bool:
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this question")

    session.delete(question)
    session.commit()
    return True