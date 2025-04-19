from fastapi import HTTPException
from sqlalchemy import select
from app.schemas.schema_quizz import QuizzGet
from sqlmodel import Session
from app.models.model_tables import Result, QuizQuestion, Question

def algo_box(length) -> QuizzGet:
    return {}

def check_answer(session: Session, question: Question, answer, quiz_id: int) -> bool:
    # Vérifie si la réponse est correcte
    is_correct = question.exercise.get("answer") == answer

    # Enregistre le résultat dans la base de données
    result = Result(
        data={"answer": answer},
        is_correct=is_correct,
        question_id=question.id
    )
    session.add(result)

    # find quiz question by quizz id and question id
    quiz_question = session.exec(
        select(QuizQuestion).where(QuizQuestion.question_id == question.id, QuizQuestion.quiz_id == quiz_id)
    ).first()
    if not quiz_question:
        raise HTTPException(status_code=404, detail="Quiz question not found")
    
    quiz_question.result_id = result.id
    
    session.commit()
    session.refresh(result)

    return is_correct