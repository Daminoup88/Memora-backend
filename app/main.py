import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from app.routers import router_account
from app.dependencies import engine
from app.config import logger
from app.routers import router_auth
from app.routers import router_patient
from app.routers import router_manager, router_questions


# Load tables to metadata
from app.models.model_tables import Account, Manager, Patient, Question, Result, Quiz, QuizQuestion

API_PREFIX = "/api"

app = FastAPI()

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

SQLModel.metadata.create_all(engine)
logger.info("Database tables created")