import logging
from passlib.context import CryptContext
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Mapping, Optional

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

    llm_enabled: bool = False
    llm_host: str = "localhost"

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

settings = Settings()

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)

pwd_context = CryptContext(schemes=[settings.password_algorithm], deprecated="auto")

json_schema_dir = "json_schema"

# LLM Config

llm_parameters = {
    "temperature": 0.3,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "num_ctx": 4096
}

llm_template = """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ .Response }}<|im_end|>
"""

llm_clues_system = """Tu es un assistant spécialisé dans la création d'indices pour des quiz destinés à des personnes atteintes d'Alzheimer. On te fournit une question et sa réponse correcte, ainsi que des questions et réponses proches pour donner du contexte.Ta tâche est de générer des indices pour aider l'utilisateur à trouver la réponse correcte. La réponse correcte ne doit pas être incluse dans les indices.
Les indices doivent être fournis uniquement sous forme de JSON, sans aucune information ou texte supplémentaire.

Voici le format d'entrée :
{
  "question": "Quel est le nom de votre premier animal de compagnie ?",
  "reponse": "Fido",
  "contexte": [
    {"question": "Qui t'a offert ton chien Fido ?", "reponse": "Marguerite"},
    {"question": "Quel est le nom de votre animal de compagnie actuel ?", "reponse": "Luna"}
  ]
}

Voici le format de sortie attendu :
{
  "indices": [
    "C'était un chien",
    "Tu l'as eu avant Milo.",
    "Marguerite te l'a offert."
  ]
}"""

llm_questions_system = """"""

class LLMSettings(BaseSettings):
    host: str = 'localhost'
    model_name: str
    is_custom: bool = False
    from_: Optional[str] = None
    parameters: Optional[Mapping[str, float]] = None
    template: Optional[str] = None
    system: Optional[str] = None

clues_model_settings = LLMSettings(host=settings.llm_host, model_name="mistral-indices", is_custom=True, from_="mistral:latest", parameters=llm_parameters, template=llm_template, system=llm_clues_system)

questions_model_settings = LLMSettings(host=settings.llm_host, model_name="mistral-questions", is_custom=True, from_="mistral:latest", parameters=llm_parameters, template=llm_template, system=llm_questions_system)

embedding_model_settings = LLMSettings(host=settings.llm_host, model_name="nomic-embed-text")