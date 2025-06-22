from sqlmodel import Session, select, func, Integer
from app.models.model_tables import QuizQuestion, Question, Result, Quiz, Patient, Account
from app.schemas.schema_question import QuestionRead
from app.schemas.schema_statistics import QuestionSuccessRate
from datetime import datetime, timedelta, date
from typing import Optional
from app.routers.router_questions import get_image_url
from fastapi import Request

def calculate_statistics(session: Session, current_account: Account, request: Request) -> dict:
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
        .where(Question.account_id == current_account.id, QuizQuestion.result_id.is_not(None))
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
        )        .select_from(QuizQuestion)
        .join(Question, QuizQuestion.question_id == Question.id)
        .join(Result, QuizQuestion.result_id == Result.id)
        .where(Question.account_id == current_account.id, QuizQuestion.result_id.is_not(None))
        .group_by(Question.category)
    ).all()
    
    category_success_rate = {
        stat.category: round((stat.correct / stat.total) * 100, 2) if stat.total > 0 else 0
        for stat in category_stats
    }
    
    # Question success rates with full question data
    question_stats = session.exec(
        select(
            Question,
            func.count().label('total'),
            func.sum(func.cast(Result.is_correct, Integer)).label('correct')
        )
        .select_from(QuizQuestion)
        .join(Question, QuizQuestion.question_id == Question.id)
        .join(Result, QuizQuestion.result_id == Result.id)
        .where(Question.account_id == current_account.id, QuizQuestion.result_id.is_not(None))
        .group_by(Question.id)
    ).all()
    
    question_success_rate = {}
    for stat in question_stats:
        question = stat[0]  # Question object
        total = stat[1]     # total attempts
        correct = stat[2]   # correct attempts
        
        success_rate = round((correct / total) * 100, 2) if total > 0 else 0
        
        # Convert Question to QuestionRead format
        question_read = QuestionRead(
            **question.model_dump(),
            image_url= get_image_url(request, question=question)
        )
        
        question_success_rate[str(question.id)] = QuestionSuccessRate(
            question=question_read,
            success_rate=success_rate
        )
    
    # Leitner box numbers - get the latest box number for each question
    # Since QuizQuestion doesn't have an id, we'll get the most recent entry per question
    leitner_stats = session.exec(
        select(
            QuizQuestion.question_id,
            QuizQuestion.box_number
        )
        .join(Question, QuizQuestion.question_id == Question.id)
        .where(Question.account_id == current_account.id, QuizQuestion.result_id.is_not(None))
        .distinct(QuizQuestion.question_id)
    ).all()
    
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

def calculate_regularity_statistics(session: Session, current_account: Account) -> dict:
    
    # Get all quiz dates for this account, ordered by date
    quiz_dates = session.exec(
        select(func.date(Quiz.created_at).label('quiz_date'))
        .join(Patient, Quiz.patient_id == Patient.id)
        .where(Patient.id == current_account.patient_id)
        .distinct()
        .order_by(func.date(Quiz.created_at))
    ).all()
    
    if not quiz_dates:
        return {
            "consecutive_days": 0,
            "quizzes_this_week": 0,
            "average_quizzes_per_week": 0.0,
            "last_quiz_date": None,
            "total_days_active": 0,
            "longest_streak": 0,
            "current_streak": 0
        }
    
    # Convert to datetime objects for easier manipulation
    dates = [quiz_date if isinstance(quiz_date, date) else date.fromisoformat(str(quiz_date)) for quiz_date in quiz_dates]
    today = datetime.now().date()
    
    # Last quiz date
    last_quiz_date = max(dates) if dates else None
    
    # Total days active
    total_days_active = len(dates)
    
    # Calculate current streak (consecutive days from today backwards)
    current_streak = 0
    check_date = today
    
    # Check if there was a quiz today or yesterday to start counting
    if last_quiz_date and (today - last_quiz_date).days <= 1:
        current_streak = 1
        check_date = last_quiz_date - timedelta(days=1)
        
        while check_date in dates:
            current_streak += 1
            check_date -= timedelta(days=1)
    
    # Calculate longest streak
    longest_streak = 0
    temp_streak = 1
    
    for i in range(1, len(dates)):
        if (dates[i] - dates[i-1]).days == 1:
            temp_streak += 1
        else:
            longest_streak = max(longest_streak, temp_streak)
            temp_streak = 1
    longest_streak = max(longest_streak, temp_streak)
    
    # Quizzes this week (from Monday to Sunday)
    today = datetime.now().date()
    days_since_monday = today.weekday()
    monday_this_week = today - timedelta(days=days_since_monday)
    sunday_this_week = monday_this_week + timedelta(days=6)
    
    quizzes_this_week = sum(1 for date in dates if monday_this_week <= date <= sunday_this_week)
    
    # Average quizzes per week
    if dates:
        first_quiz_date = min(dates)
        days_since_first_quiz = (today - first_quiz_date).days + 1
        weeks_since_first_quiz = max(1, days_since_first_quiz / 7)
        average_quizzes_per_week = round(total_days_active / weeks_since_first_quiz, 1)
    else:
        average_quizzes_per_week = 0.0
    
    return {
        "consecutive_days": current_streak,
        "quizzes_this_week": quizzes_this_week,
        "average_quizzes_per_week": average_quizzes_per_week,
        "last_quiz_date": datetime.combine(last_quiz_date, datetime.min.time()) if last_quiz_date else None,
        "total_days_active": total_days_active,
        "longest_streak": longest_streak,
        "current_streak": current_streak
    }
