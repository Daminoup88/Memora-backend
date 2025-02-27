from sqlmodel import Session, create_engine
from app.database import database
from typing import Generator
from app.models.model_tables import Account
from app.crud.crud_account import read_account_by_id, read_account_by_username
from app.config import pwd_context, oauth2_scheme, secret_key, algorithm
import jwt
from jwt import InvalidTokenError
from fastapi import HTTPException, status, Depends
from typing import Annotated

# Database
engine = create_engine(database.DATABASE_URL)

def get_session() -> Generator[Session, None, None]: # pragma: no cover
    with Session(engine) as session:
        yield session

# Authentication
def authenticate_account(session: Session, email: str, password: str) -> Account:
    account = read_account_by_username(session, email)
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
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_current_account(token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    try:
        payload = jwt.decode(token, secret_key, algorithms=algorithm)
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