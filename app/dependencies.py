from sqlmodel import Session, create_engine
from sqlalchemy import select
from app.database import database
from typing import Generator
from app.models.model_tables import Account, Manager, Question, Quiz, Result, QuizQuestion
from app.crud.crud_account import read_account_by_id, read_account_by_username
from app.config import pwd_context, settings, json_schema_dir
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import InvalidTokenError
from fastapi import HTTPException, status, Depends
from typing import Annotated
import os
import json
from jsonschema import validate, ValidationError
from app.schemas.schema_question import QuestionCreate, QuestionUpdate
from app.schemas.schema_quiz import ResultRead
from pydantic import ValidationError as PydanticValidationError

# Database
engine = create_engine(database.DATABASE_URL)

def get_session() -> Generator[Session, None, None]: # pragma: no cover
    with Session(engine) as session:
        yield session

# Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def authenticate_account(session: Session, username: str, password: str) -> Account:
    account = read_account_by_username(session, username)
    if not account:
        return None
    if not verify_password(password, account.password_hash):
        return None
    return account

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    to_encode["sub"] = str(to_encode["sub"])
    return jwt.encode(to_encode, settings.token_secret_key, algorithm=settings.token_algorithm)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_current_account(token: Annotated[str, Depends(oauth2_scheme)], session: Annotated[Session, Depends(get_session)]) -> Account:
    try:
        payload = jwt.decode(token, settings.token_secret_key, algorithms=settings.token_algorithm)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not payload["sub"].isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    account = read_account_by_id(session, int(payload["sub"]))
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

# Manager checks

class ManagerChecker:
    def __init__(self):
        pass

    def __call__(self, manager_id: int, session: Annotated[Session, Depends(get_session)], current_account: Annotated[Account, Depends(get_current_account)]) -> Manager:
        manager = session.get(Manager, manager_id)
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        if manager.account_id != current_account.id:
            raise HTTPException(status_code=403, detail="Not authorized to perform this action")
        return manager

manager_checker = ManagerChecker()

def get_current_manager(manager: Annotated[Manager, Depends(manager_checker)]) -> Manager:
    return manager

# Question checks

class CheckerBase:
    def __init__(self, schema_dir: str):
        self.schemas = {}
        self.schema_dir = schema_dir
        for schema_file in os.listdir(self.schema_dir):
            if schema_file.endswith(".json"):
                schema_name = schema_file.split(".")[0]
                with open(os.path.join(self.schema_dir, schema_file), "r") as file:
                    self.schemas[schema_name] = json.load(file)

    def validate_schema(self, instance: dict, schema_type: str):
        schema = self.schemas.get(schema_type)
        if not schema:
            raise HTTPException(status_code=400, detail=f"Unsupported type: {schema_type}")
        validate(instance=instance, schema=schema)

class ExerciseChecker(CheckerBase):
    def __init__(self):
        super().__init__(os.path.join(json_schema_dir, "questions"))

    def __call__(self, question: QuestionCreate | QuestionUpdate) -> QuestionCreate | QuestionUpdate:
        try:
            self.validate_schema(question.exercise, question.type)
            self.additional_validation(question)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid format for type '{question.type}': {e.message}")
        except KeyError as e:
            raise HTTPException(status_code=422, detail=f"Missing field: {e}")
        return question

    def additional_validation(self, question: QuestionCreate | QuestionUpdate) -> None:
        if question.type == "missing_words":
            num_words = len(question.exercise["answers"])
            pipe_count = question.exercise["question"].count('|')
            if pipe_count != 2 * num_words:
                raise ValidationError(f"expected {num_words} words, but found {pipe_count // 2} pipe pairs")

exercise_checker = ExerciseChecker()

def get_validated_question(question: Annotated[QuestionCreate | QuestionUpdate, Depends(exercise_checker)]) -> QuestionCreate | QuestionUpdate:
    try:
        return exercise_checker(question)
    except PydanticValidationError as e:
        # Validation de schéma Pydantic (champs requis, types) => 422
        raise HTTPException(status_code=422, detail=e.errors())
    except ValidationError as e:
        # Validation métier (jsonschema) => 400
        raise HTTPException(status_code=400, detail=f"Invalid format for type '{getattr(question, 'type', None)}': {e.message}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class QuestionChecker:
    def __init__(self):
        pass

    def __call__(self, session: Annotated[Session, Depends(get_session)], current_account: Annotated[Account, Depends(get_current_account)], question_id: int | None = None) -> Question:
        if question_id is None:
            return None
        question = session.get(Question, question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        if question.account_id != current_account.id:
            raise HTTPException(status_code=403, detail="Not authorized to perform this action")
        return question

question_checker = QuestionChecker()
    
def get_current_question(question: Annotated[Question, Depends(question_checker)]) -> Question:
    return question

class QuizChecker:
    def __init__(self):
        pass

    def __call__(self, session: Annotated[Session, Depends(get_session)], current_account: Annotated[Account, Depends(get_current_account)], quiz_id: int) -> Quiz:
        quiz = session.get(Quiz, quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        if quiz.patient_id != current_account.patient_id:
            raise HTTPException(status_code=403, detail="Not authorized to perform this action")
        return quiz
    
quiz_checker = QuizChecker()

def get_current_quiz(quiz: Annotated[Quiz, Depends(quiz_checker)]) -> Quiz:
    return quiz

class AnswerChecker(CheckerBase):
    def __init__(self):
        super().__init__(os.path.join(json_schema_dir, "answers"))

    def __call__(self, answer: ResultRead, current_question: Annotated[Question, Depends(get_current_question)], current_quiz: Annotated[Quiz, Depends(get_current_quiz)], session: Annotated[Session, Depends(get_session)]) -> Result:
        if not current_question:
            raise HTTPException(status_code=400, detail="question_id query parameter required")
        quiz_question = session.exec(
            select(QuizQuestion).where(QuizQuestion.question_id == current_question.id, QuizQuestion.quiz_id == current_quiz.id)
        ).scalars().first()
        if not quiz_question:
            raise HTTPException(status_code=404, detail=f"The question {current_question.id} is not in the quiz {current_quiz.id}")
        if quiz_question.result_id is not None:
            raise HTTPException(status_code=400, detail="Answer already submitted for this question in the quiz")

        try:
            self.validate_schema(answer.data, current_question.type)
            self.additional_validation(answer, current_question)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid format for type '{current_question.type}': {e.message}")
        self.answer_check(answer, current_question)
        result = Result(
            data=answer.data,
            is_correct=answer.is_correct
        )
        return result
    
    def additional_validation(self, answer: ResultRead, question: Question) -> None:
        if question.type == "missing_words":
            num_words = len(answer.data["answers"])
            pipe_count = question.exercise["question"].count('|')
            if pipe_count != 2 * num_words:
                raise ValidationError(f"expected {num_words} words, but found {pipe_count // 2} pipe pairs")
            
    def answer_check(self, answer: ResultRead, question: Question) -> bool:
        pass

answer_checker = AnswerChecker()

def get_validated_answer(answer: Annotated[Result, Depends(answer_checker)]) -> Result:
    return answer