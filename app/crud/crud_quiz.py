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
    ).scalars().all()

    # SELECT q.*
    # FROM Question q
    # JOIN QuizQuestion qq ON q.id = qq.question_id
    # JOIN (
    #     SELECT question_id, MAX(quiz_id) as max_quiz_id
    #     FROM QuizQuestion
    #     GROUP BY question_id
    # ) latest_qq ON qq.quiz_id = latest_qq.max_quiz_id AND qq.question_id = latest_qq.question_id
    # JOIN LeitnerParameters lp ON qq.box_number = lp.box_number
    # JOIN Quiz qz ON qz.id = qq.quiz_id
    # WHERE q.account_id = 9
    # AND qz.created_at < (CURRENT_TIMESTAMP - lp.leitner_delay)
    # ORDER BY qq.box_number ASC
    # LIMIT 10;
    leitner_questions = session.exec(
        select(Question).where(
            Question.account_id == current_account.id
        ).join(
            QuizQuestion, QuizQuestion.question_id == Question.id
        ).where(
            QuizQuestion.quiz_id == (
                select(func.max(QuizQuestion.quiz_id)).where(
                    QuizQuestion.question_id == Question.id
                ).correlate(Question).scalar_subquery()
            )
        ).join(
            LeitnerParameters, QuizQuestion.box_number == LeitnerParameters.box_number
        ).join(
            Quiz, Quiz.id == QuizQuestion.quiz_id
        ).where(
            Quiz.created_at < func.now() - LeitnerParameters.leitner_delay
        ).order_by(
            QuizQuestion.box_number.asc()
        ).limit(number_of_questions - len(never_answered))
    ).scalars().all()
    
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
        if quiz_question.box_number is None:
            quiz_question.box_number = 1
        questions_read.append(QuestionRead(**question.model_dump()))
        session.add(quiz_question)
    session.commit()

    return QuizRead(id=new_quiz.id, questions=questions_read)

def read_quiz_by_id(current_quiz: Quiz, session: Session) -> QuizRead:
    # SELECT * FROM Question q WHERE q.id IN (SELECT question_id FROM QuizQuestion qq WHERE qq.quiz_id = :quiz_id)
    questions = session.exec(
        select(Question).where(
            Question.id.in_(
                select(QuizQuestion.question_id).where(
                    QuizQuestion.quiz_id == current_quiz.id
                )
            )
        )
    ).scalars().all()

    return QuizRead(id=current_quiz.id, questions=questions)

def save_answer(answer: Result, current_quiz: Quiz, question: Question, session: Session) -> ResultRead:
    # SELECT * FROM QuizQuestion qq WHERE qq.question_id = :question_id AND qq.quiz_id = :quiz_id
    quiz_question = session.exec(
        select(QuizQuestion).where(QuizQuestion.question_id == question.id, QuizQuestion.quiz_id == current_quiz.id)
    ).scalars().first()

    session.add(answer)
    session.commit()
    session.refresh(answer)
    
    quiz_question.result_id = answer.id
    if answer.is_correct:
        quiz_question.box_number = min(quiz_question.box_number + 1, 7)
    else:
        quiz_question.box_number = 1
    session.add(quiz_question)
    session.commit()
    session.refresh(quiz_question)
    return answer