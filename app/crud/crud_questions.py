from sqlmodel import Session, select
from fastapi import HTTPException
from app.models.model_tables import Question, Account, Manager

def create_question(session: Session, question: Question, current_account: Account, manager_id: int) -> Question:
    manager = session.get(Manager, manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    if manager.account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")
    session.add(question)
    session.commit()
    session.refresh(question)
    return question

def read_questions(session: Session, current_account: Account, manager_id: int) -> list[Question]:
    manager = session.get(Manager, manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    if manager.account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")
    return session.exec(select(Question)).all()

def read_question_by_id(session: Session, question_id: int, current_account: Account, manager_id: int) -> Question:
    manager = session.get(Manager, manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    if manager.account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

def update_question(session: Session, question_id: int, question_data: Question, current_account: Account, manager_id: int) -> Question:
    manager = session.get(Manager, manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    if manager.account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    for key, value in question_data.model_dump().items():
        setattr(question, key, value)

    session.commit()
    session.refresh(question)
    return question

def delete_question(session: Session, question_id: int, current_account: Account, manager_id: int) -> bool:
    manager = session.get(Manager, manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    if manager.account_id != current_account.id:
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    session.delete(question)
    session.commit()
    return True