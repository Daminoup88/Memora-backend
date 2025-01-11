import logging
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

secret_key = "SECRET_KEY"
algorithm = "HS256"