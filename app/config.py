import logging
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    database_driver: str
    database_host: str
    database_port: int
    database_user: str
    database_password: str
    database_name: str

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

secret_key = "SECRET_KEY"
algorithm = "HS256"

settings = Settings()