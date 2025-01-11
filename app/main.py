import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from contextlib import asynccontextmanager
from app.routers import users
from app.dependencies import engine
from app.config import logger
from app.routers import auth

API_PREFIX = "/api"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/random")
def read_random():
    r = random.randint(1, 100)
    logger.debug(f"Generated random number: {r}")
    return {"random": r}

app.include_router(users.router, prefix=f"{API_PREFIX}/users", tags=["users"])
app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["auth"])

SQLModel.metadata.create_all(engine)
logger.info("Database tables created")