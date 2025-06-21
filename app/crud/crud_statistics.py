from sqlmodel import Session, select, func, Integer
from app.models.model_tables import QuizQuestion, Question, Result

def calculate_statistics(session: Session, account_id: int) -> dict:
    """
    Calculate statistics using pure SQL aggregations to avoid N+1 queries.
    All calculations are done in the database for optimal performance.
    """
    
    # Global statistics - count total attempts and correct answers
    global_stats = session.exec(
        select(
            func.count().label('total_attempts'),
            func.sum(func.cast(Result.is_correct, Integer)).label('correct_answers')
        )
        .select_from(QuizQuestion)
        .join(Question, QuizQuestion.question_id == Question.id)
        .join(Result, QuizQuestion.result_id == Result.id)
        .where(Question.account_id == account_id, QuizQuestion.result_id.is_not(None))
    ).first()
    
    global_attempts = global_stats.total_attempts or 0
    global_correct = global_stats.correct_answers or 0
    global_success_rate = round((global_correct / global_attempts) * 100, 2) if global_attempts > 0 else 0
    
    # Category success rates - aggregated by category
    category_stats = session.exec(
        select(
            Question.category,
            func.count().label('total'),
            func.sum(func.cast(Result.is_correct, Integer)).label('correct')
        )
        .select_from(QuizQuestion)
        .join(Question, QuizQuestion.question_id == Question.id)
        .join(Result, QuizQuestion.result_id == Result.id)
        .where(Question.account_id == account_id, QuizQuestion.result_id.is_not(None))
        .group_by(Question.category)
    ).all()
    
    category_success_rate = {
        stat.category: round((stat.correct / stat.total) * 100, 2) if stat.total > 0 else 0
        for stat in category_stats    }
    
    # Question success rates - aggregated by question_id
    question_stats = session.exec(
        select(
            Question.id,
            func.count().label('total'),
            func.sum(func.cast(Result.is_correct, Integer)).label('correct')
        )
        .select_from(QuizQuestion)
        .join(Question, QuizQuestion.question_id == Question.id)
        .join(Result, QuizQuestion.result_id == Result.id)
        .where(Question.account_id == account_id, QuizQuestion.result_id.is_not(None))
        .group_by(Question.id)
    ).all()
    
    question_success_rate = {
        stat.id: round((stat.correct / stat.total) * 100, 2) if stat.total > 0 else 0
        for stat in question_stats    }
    
    # Leitner box numbers - get the latest box number for each question
    # Since QuizQuestion doesn't have an id, we'll get the most recent entry per question
    leitner_stats = session.exec(
        select(
            QuizQuestion.question_id,
            QuizQuestion.box_number
        )
        .join(Question, QuizQuestion.question_id == Question.id)
        .where(Question.account_id == account_id, QuizQuestion.result_id.is_not(None))
        .distinct(QuizQuestion.question_id)    ).all()
    
    # Keep the box number for each question (distinct already handles uniqueness)
    leitner_box_numbers = {
        stat.question_id: stat.box_number 
        for stat in leitner_stats 
        if stat.box_number is not None
    }

    return {
        "global_success_rate": global_success_rate,
        "category_success_rate": category_success_rate,
        "question_success_rate": question_success_rate,
        "leitner_box_numbers": leitner_box_numbers,
    }
