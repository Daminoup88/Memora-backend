from sqlmodel import SQLModel
from datetime import datetime
from app.schemas.schema_pagination import PaginatedResponse
from pydantic import BaseModel
from typing import Type, Union
import random

class QuestionCreate(SQLModel):
    type: str
    category: str
    exercise: dict

class QuestionRead(SQLModel):
    id: int
    type: str
    category: str
    exercise: dict
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None
    edited_by: int | None = None
    image_url: str | None = None

class QuestionUpdate(QuestionCreate):
    pass

class Clues(SQLModel):
    clues: list[str]

class RawDataRead(SQLModel):
    id: int
    text: str
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None
    edited_by: int | None = None
    image_url: str | None = None

class QuestionExercise(SQLModel):
    question: str
    answer: str

class MultipleChoiceQuestionExercise(SQLModel):
    question: str
    choices: list[str]
    answer: str

class MissingWordsExercise(SQLModel):
    question: str
    answers: list[str]

class MatchElementsExercise(SQLModel):
    pairs: dict[str, str]

class ChronologicalOrderExercise(SQLModel):
    ordered: list[str]

############################################

class SimpleQuestionGenerate(BaseModel):
    exercise: QuestionExercise
    image_path: str | None = None

class MCQQuestionGenerate(BaseModel):
    exercise: MultipleChoiceQuestionExercise
    image_path: str | None = None

class MissingWordsQuestionGenerate(BaseModel):
    exercise: MissingWordsExercise
    image_path: str | None = None

class MatchElementsQuestionGenerate(BaseModel):
    exercise: MatchElementsExercise
    image_path: str | None = None

class ChronologicalOrderQuestionGenerate(BaseModel):
    exercise: ChronologicalOrderExercise
    image_path: str | None = None

# Mapping des types d'exercices vers leurs classes et consignes pour le LLM
EXERCISE_TYPE_MAPPING = {
    "question": {
        "class": SimpleQuestionGenerate,
        "prompt": "Génère une question ouverte simple avec une réponse textuelle courte. Exemple: {\"question\": \"Quelle est la couleur du ciel ?\", \"answer\": \"Bleu\"}\n"
    },
    "mcq": {
        "class": MCQQuestionGenerate,
        "prompt": "Génère une question à choix multiple avec 3-4 options. Exemple: {\"question\": \"Quelle est la capitale de la France ?\", \"choices\": [\"Paris\", \"Londres\", \"Berlin\"], \"answer\": \"Paris\"}\n"
    },
    "missing_words": {
        "class": MissingWordsQuestionGenerate,
        "prompt": "Génère une question avec des mots manquants marqués par ||. Puis dans les réponses, donne les mots manquants. Exemple: {\"question\": \"Le Sahara est un || situé en ||.\", \"answers\": [\"désert\", \"Afrique\"]}\n"
    },
    "match_elements": {
        "class": MatchElementsQuestionGenerate,
        "prompt": "Génère une question d'association d'éléments. Format JSON sous forme de dictionnaire: Exemple: {\"Chien\": \"Animal de compagnie\", \"Paris\": \"Capitale de la France\"}\n"
    },
    "chronological_order": {
        "class": ChronologicalOrderQuestionGenerate,
        "prompt": "Génère une question d'ordre chronologique. Format JSON: {\"ordered\": [\"événement1\", \"événement2\", \"événement3\"]} dans l'ordre chronologique correct\n"
    }
}

class QuestionGenerate(BaseModel):
    type: str
    prompt: str
    question_class: Type[Union[SimpleQuestionGenerate, MCQQuestionGenerate, MissingWordsQuestionGenerate, MatchElementsQuestionGenerate, ChronologicalOrderQuestionGenerate]]

def get_random_typed_question_create() -> QuestionGenerate:
    question_type = random.choice(list(EXERCISE_TYPE_MAPPING.keys()))
    question_class = EXERCISE_TYPE_MAPPING[question_type]["class"]
    prompt = EXERCISE_TYPE_MAPPING[question_type]["prompt"]
    return QuestionGenerate(
        type=question_type,
        prompt=prompt,
        question_class=question_class
    )

# Alias pour la réponse paginée de questions
PaginatedQuestionsResponse = PaginatedResponse[QuestionRead]