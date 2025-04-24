import logging
from passlib.context import CryptContext
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    database_driver: str
    database_host: str
    database_port: int
    database_user: str
    database_password: str
    database_name: str

    token_secret_key: str
    token_algorithm: str

    password_algorithm: str

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

settings = Settings()

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)

pwd_context = CryptContext(schemes=[settings.password_algorithm], deprecated="auto")

json_schema_dir = "json_schema"