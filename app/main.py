import random
from fastapi import FastAPI
from app.routers import users
from sqlmodel import SQLModel
from app.dependencies import engine
from contextlib import asynccontextmanager
from app.config import logger
from fastapi.middleware.cors import CORSMiddleware

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

app.include_router(users.router, prefix="/api", tags=["users"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created")
    yield