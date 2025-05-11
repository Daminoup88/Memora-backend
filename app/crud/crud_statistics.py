from sqlmodel import Session, select
from app.models.model_tables import QuizQuestion, Question, Result

def calculate_statistics(session: Session, account_id: int) -> dict:
    # Fetch all QuizQuestion entries for the account
    quiz_questions = session.exec(
        select(QuizQuestion).join(Question).where(Question.account_id == account_id, QuizQuestion.result_id.is_not(None))
    ).all()

    global_attempts = len(quiz_questions)
    global_correct = sum(
        1 for qq in quiz_questions if qq.result_id and session.get(Result, qq.result_id).is_correct
    )
    global_success_rate = round((global_correct / global_attempts) * 100, 2) if global_attempts > 0 else 0

    category_success_rate = {}
    question_success_rate = {}
    leitner_box_numbers = {}

    for qq in quiz_questions:
        question = session.get(Question, qq.question_id)
        result = session.get(Result, qq.result_id) if qq.result_id else None

        # Success rate per category
        if question.category not in category_success_rate:
            category_success_rate[question.category] = {"correct": 0, "total": 0}
        if result and result.is_correct:
            category_success_rate[question.category]["correct"] += 1
        category_success_rate[question.category]["total"] += 1

        # Success rate per question
        if question.id not in question_success_rate:
            question_success_rate[question.id] = {"correct": 0, "total": 0}
        if result and result.is_correct:
            question_success_rate[question.id]["correct"] += 1
        question_success_rate[question.id]["total"] += 1

        # Leitner box numbers
        leitner_box_numbers[question.id] = qq.box_number

    # Finalize category and question success rates
    category_success_rate = {
        category: round((data["correct"] / data["total"]) * 100, 2) if data["total"] > 0 else 0
        for category, data in category_success_rate.items()
    }
    question_success_rate = {
        question_id: round((data["correct"] / data["total"]) * 100, 2) if data["total"] > 0 else 0
        for question_id, data in question_success_rate.items()
    }

    return {
        "global_success_rate": global_success_rate,
        "category_success_rate": category_success_rate,
        "question_success_rate": question_success_rate,
        "leitner_box_numbers": leitner_box_numbers,
    }
