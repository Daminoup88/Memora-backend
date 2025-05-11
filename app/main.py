import random
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Session, select, func
from app.routers import router_account
from app.dependencies import engine
from app.config import logger
from app.routers import router_auth
from app.routers import router_patient
from app.routers import router_manager, router_questions
from sqlalchemy.exc import IntegrityError
from contextlib import asynccontextmanager
from sqlalchemy import cast, String
import json
from app.routers import router_default_questions
from app.routers import router_quiz
from app.routers import router_statistics

# Load tables to metadata
from app.models.model_tables import Account, Manager, Patient, Question, Result, Quiz, QuizQuestion, DefaultQuestions , LeitnerParameters

# Unique IDs for routes for frontend client generation
# !!! All the routes must have unique names !!!
def custom_generate_unique_id(route: APIRoute):
    return route.name

API_PREFIX = "/api"

@asynccontextmanager
async def lifespan(app: FastAPI):
    populate_default_questions()
    populate_leitner_parameters()
    yield
    # Add any cleanup logic here if needed

app = FastAPI(generate_unique_id_function=custom_generate_unique_id, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uncomment the following lines to enable HTTPS redirection
# from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
# app.add_middleware(HTTPSRedirectMiddleware)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/random")
def read_random():
    r = random.randint(1, 100)
    logger.debug(f"Generated random number: {r}")
    return {"random": r}

app.include_router(router_account.router, prefix=f"{API_PREFIX}/accounts", tags=["account"])
app.include_router(router_auth.router, prefix=f"{API_PREFIX}/auth", tags=["auth"])
app.include_router(router_patient.router, prefix=f"{API_PREFIX}/patients", tags=["patient"])
app.include_router(router_manager.router, prefix=f"{API_PREFIX}/managers", tags=["manager"])
app.include_router(router_questions.router, prefix=f"{API_PREFIX}/questions", tags=["question"])
app.include_router(router_default_questions.router, prefix=f"{API_PREFIX}/default-questions", tags=["default-questions"])
app.include_router(router_quiz.router, prefix=f"{API_PREFIX}/quiz", tags=["quiz"])
app.include_router(router_statistics.router, prefix=f"{API_PREFIX}/statistics", tags=["statistics"])

SQLModel.metadata.create_all(engine)
logger.info("Database tables created")

def populate_default_questions():
    with open("app/data/default_questions.json", "r", encoding="utf-8") as file:
        default_questions = json.load(file)

    with Session(engine) as session:
        table_count = len(session.exec(select(DefaultQuestions)).all())
        list_count = len(default_questions)

        if table_count != list_count:
            logger.info(f"Populating default questions. Table count: {table_count}, List count: {list_count}")
            session.exec(DefaultQuestions.__table__.delete())
            session.commit()

            for question in default_questions:
                session.add(DefaultQuestions(**question))
            session.commit()

def populate_leitner_parameters():
    delays = ["1 day", "2 days", "3 days", "4 days", "7 days", "14 days", "30 days"]
    with Session(engine) as session:
        table_count = session.exec(select(func.count(LeitnerParameters.box_number))).first()
        if table_count == 0:
            for i, delay in enumerate(delays):
                session.add(LeitnerParameters(box_number=i+1, leitner_delay=delay))
            session.commit()
            logger.info("Leitner parameters populated")