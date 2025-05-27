from fastapi import HTTPException
from sqlalchemy import select, func
from app.schemas.schema_question import QuestionRead
from app.schemas.schema_quiz import QuizRead, ResultRead
from sqlmodel import Session
from app.models.model_tables import Result, QuizQuestion, Question, Quiz, Account, LeitnerParameters
import base64

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

def _get_image_url(base_url, question):
    if question.image_path:
        return f"{base_url}api/questions/{question.id}/image"
    return None

def create_leitner_quiz(number_of_questions: int, current_account: Account, session: Session, base_url: str) -> QuizRead:
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
    leitner_data = session.exec(
        select(Question, QuizQuestion.box_number).where(
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
    ).all()
    
    leitner_questions = []
    leitner_boxes = {}
    for question, box_number in leitner_data:
        leitner_boxes[question.id] = box_number
        leitner_questions.append(question)

    questions = never_answered + leitner_questions

    if not questions:
        raise HTTPException(status_code=404, detail="No quiz available")

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
        if leitner_boxes.get(question.id) is None:
            quiz_question.box_number = 1
        else:
            quiz_question.box_number = leitner_boxes[question.id]
        q_dict = question.model_dump()
        q_dict["image_path"] = question.image_path  # optionnel, à retirer si inutile côté client
        q_dict["image_url"] = _get_image_url(base_url, question)  # lien public pour accès image
        questions_read.append(QuestionRead(**q_dict))
        session.add(quiz_question)
    session.commit()

    return QuizRead(id=new_quiz.id, questions=questions_read)

def get_latest_quiz_remaining_questions(current_account: Account, session: Session, base_url: str) -> QuizRead:
    # SELECT id FROM Quiz q WHERE q.patient_id = :patient_id ORDER BY id DESC LIMIT 1
    latest_quiz_id = session.exec(
        select(Quiz.id).where(
            Quiz.patient_id == current_account.patient_id
        ).order_by(
            Quiz.id.desc()
        ).limit(1)
    ).scalars().first()
    if not latest_quiz_id:
        return None

    # SELECT * FROM Question q WHERE q.id IN (SELECT question_id FROM QuizQuestion qq WHERE qq.quiz_id = :quiz_id AND qq.result_id IS NULL)
    questions = session.exec(
        select(Question).where(
            Question.id.in_(
                select(QuizQuestion.question_id).where(
                    QuizQuestion.quiz_id == latest_quiz_id,
                    QuizQuestion.result_id.is_(None)
                )
            )
        )
    ).scalars().all()

    if not questions:
        return None
    questions_read = []
    for question in questions:
        q_dict = question.model_dump()
        q_dict["image_path"] = question.image_path
        q_dict["image_url"] = _get_image_url(base_url, question)
        questions_read.append(QuestionRead(**q_dict))
    return QuizRead(id=latest_quiz_id, questions=questions_read)

def read_quiz_by_id(current_quiz: Quiz, session: Session, base_url: str) -> QuizRead:
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

    questions_read = []
    for question in questions:
        q_dict = question.model_dump()
        q_dict["image_path"] = question.image_path
        q_dict["image_url"] = _get_image_url(base_url, question)
        questions_read.append(QuestionRead(**q_dict))
    return QuizRead(id=current_quiz.id, questions=questions_read)

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