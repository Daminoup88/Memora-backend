from sqlmodel import Session, create_engine
from app.database import database
from typing import Generator
from app.models.model_tables import Account, Manager, Question
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

class ExerciseChecker:
    def __init__(self):
        self.schemas = {}
        for schema_file in os.listdir(json_schema_dir):
            if schema_file.endswith(".json"):
                schema_name = schema_file.split(".")[0]
                with open(os.path.join(json_schema_dir, schema_file), "r") as file:
                    self.schemas[schema_name] = json.load(file)

    def __call__(self, question: QuestionCreate | QuestionUpdate) -> QuestionCreate | QuestionUpdate:
        schema = self.schemas.get(question.type)
        if not schema:
            raise HTTPException(status_code=400, detail=f"Unsupported question type: {question.type}")

        try:
            validate(instance=question.exercise, schema=schema)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid exercise format for type '{question.type}': {e.message}")
        
        return question

exercise_checker = ExerciseChecker()

def get_validated_question(question: Annotated[QuestionCreate | QuestionUpdate, Depends(exercise_checker)]) -> QuestionCreate | QuestionUpdate:
    return question

class QuestionChecker:
    def __init__(self):
        pass

    def __call__(self, question_id: int, session: Annotated[Session, Depends(get_session)], current_account: Annotated[Account, Depends(get_current_account)]) -> Question:
        question = session.get(Question, question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        if question.account_id != current_account.id:
            raise HTTPException(status_code=403, detail="Not authorized to perform this action")
        return question

question_checker = QuestionChecker()
    
def get_current_question(question: Annotated[Question, Depends(question_checker)]) -> Question:
    return question