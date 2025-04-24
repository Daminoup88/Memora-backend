from fastapi import HTTPException
from sqlalchemy import select, func
from app.schemas.schema_question import QuestionRead
from app.schemas.schema_quiz import QuizRead, ResultRead
from sqlmodel import Session
from app.models.model_tables import Result, QuizQuestion, Question, Quiz, Account, LeitnerParameters

def have_all_questions_been_answered(current_account: Account, session: Session) -> bool:
    # SELECT COUNT(*) FROM Question q WHERE account_id = :account_id AND id IN (SELECT question_id FROM QuizQuestion qq WHERE qq.question_id = q.id AND qq.result_id IS NULL)
    never_answered = session.exec(
        select(Question).where(
            Question.account_id == current_account.id,
            Question.id.in_(
                select(QuizQuestion.question_id).where(
                    QuizQuestion.result_id.is_(None)
                )
            )
        )
    ).first()
    return never_answered == None

def create_leitner_quiz(number_of_questions: int, current_account: Account, session: Session) -> QuizRead:
    # SELECT * FROM Question WHERE account_id = :account_id AND id NOT IN (SELECT question_id FROM QuizQuestion)
    never_answered = session.exec(
        select(Question).where(
            Question.account_id == current_account.id,
            Question.id.not_in(
                select(QuizQuestion.question_id)
            )
        )
    ).all()

    # SELECT q.* FROM Question q
    # WHERE q.account_id = :account_id
    # (eventually) AND q.id NOT IN (SELECT question_id FROM QuizQuestion WHERE result_id IS NULL)
    # JOIN QuizQuestion qq ON q.id = qq.question_id
    # WHERE qq.id = (SELECT MAX(id) FROM QuizQuestion WHERE question_id = q.id)
    # JOIN LeitnerParameters lp ON lp.box_number = qq.box_number
    # JOIN Quiz qz ON qz.id = qq.quiz_id AND qz.created_at < DATEADD(DAY, -lp.leitner_delay, GETDATE())
    # ORDER BY lp.box_number ASC, qq.last_answer_date ASC
    # LIMIT :number_of_questions
    leitner_questions = session.exec(
        select(Question).where(
            Question.account_id == current_account.id
        ).join(
            QuizQuestion, QuizQuestion.question_id == Question.id
        ).where(
            QuizQuestion.id == (
                select(func.max(QuizQuestion.id)).where(
                    QuizQuestion.question_id == Question.id
                )
            )
        ).join(
            LeitnerParameters, QuizQuestion.box_number == LeitnerParameters.box_number
        ).join(
            Quiz, Quiz.id == QuizQuestion.quiz_id
        ).where(
            Quiz.created_at < func.now() - LeitnerParameters.leitner_delay
        ).order_by(
            QuizQuestion.box_number.asc()
        )
    ).limit(number_of_questions - len(never_answered)).all()
    
    questions = never_answered + leitner_questions

    new_quiz = Quiz(patient_id=current_account.patient_id)
    session.add(new_quiz)
    session.commit()
    session.refresh(new_quiz)

    questions_read = []

    for question in questions:
        quiz_question = QuizQuestion(
            quiz_id=new_quiz.id,
            question_id=question.id
        )
        questions_read.append(QuestionRead(**question.model_dump()))
        session.add(quiz_question)
    session.commit()

    return QuizRead(id=new_quiz.id, questions=questions_read)


def save_answer(answer: Result, current_quiz: Quiz, question: Question, session: Session) -> ResultRead:
    # SELECT * FROM QuizQuestion qq WHERE qq.question_id = :question_id AND qq.quiz_id = :quiz_id
    quiz_question = session.exec(
        select(QuizQuestion).where(QuizQuestion.question_id == question.id, QuizQuestion.quiz_id == current_quiz.id)
    ).first()

    session.add(answer)
    session.commit()
    session.refresh(answer)
    
    quiz_question.result_id = answer.id
    if answer.is_correct:
        quiz_question.box_number += 1
    else:
        quiz_question.box_number = 1
    session.add(quiz_question)
    session.commit()
    session.refresh(quiz_question)
    return answer