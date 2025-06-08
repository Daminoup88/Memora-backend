from ollama import AsyncClient, Client, RequestError, ResponseError
from app.config import logger, LLMSettings
import asyncio
import sys
from functools import wraps
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError
import time

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class LLMModel(AsyncClient):
    def __init__(self, settings: LLMSettings):
        self.host = settings.host
        super().__init__(host=self.host)
        self.sync_client = Client(host=self.host)
        self.model_name = settings.model_name
        self.is_custom = settings.is_custom
        self.is_initialized = False
        if self.is_custom:
            self.from_ = settings.from_
            self.parameters = settings.parameters
            self.template = settings.template
            self.system = settings.system
        self.initialize()

    def initialize(self):
        if self.is_initialized:
            return
        
        if not self.is_custom:
            self.pull_model_if_not_exists()
        else:
            self.create_model_if_not_exists()
        
        self.is_initialized = True
    
    @staticmethod
    def manage_llm_errors(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ConnectionError as e:
                logger.error(f"LLM connection error: {e}")
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM Unavailable: Connection error")
            except RequestError as e:
                logger.error(f"LLM request error: {e}")
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM Unavailable: Request error")
            except ResponseError as e:
                logger.error(f"LLM response error: {e}")
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM Unavailable: Response error")
            except Exception as e:
                logger.error(f"LLM Error: {e}")
                raise
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"LLM Error: {e}")
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM Unavailable: General error")
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    @manage_llm_errors
    def create_model_if_not_exists(self):
        if self.model_exists():
            logger.info(f"Model '{self.model_name}' already exists.")
        else:
            logger.info(f"Creating model '{self.model_name}'...")
            logger.info("This may take a while, please wait...")
            self.sync_client.create(self.model_name, from_=self.from_, parameters=self.parameters, template=self.template, system=self.system)
            logger.info(f"Model '{self.model_name}' created successfully.")

    @manage_llm_errors
    def pull_model_if_not_exists(self):
        if self.model_exists():
            logger.info(f"Model '{self.model_name}' already exists.")
        else:
            logger.info(f"Pulling model '{self.model_name}'...")
            logger.info("This may take a while, please wait...")
            self.sync_client.pull(self.model_name)
            logger.info(f"Model '{self.model_name}' pulled successfully.")

    @manage_llm_errors
    async def generate(self, prompt: str, format: type[BaseModel] = None, **kwargs):
        kwargs['model'] = self.model_name
        if format is not None:
            response = await super().generate(prompt=prompt, format=format.model_json_schema(), **kwargs)
            try:
                formatted = format.model_validate_json(response['response'])
                return formatted
            except ValidationError as e:
                logger.error(f"LLM validation error: {e}")
                raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail=f"LLM validation Error: {e}")
        response = await super().generate(prompt=prompt, **kwargs)
        return response['response']
    
    @manage_llm_errors
    async def embed(self, prompt: str, **kwargs):
        kwargs['model'] = self.model_name
        response = await super().embed(input=prompt, **kwargs)
        return response['embeddings'][0]

    def model_exists(self) -> bool:
        tries = 0
        while True:
            try:
                models = self.sync_client.list()
                return any(model['model'] == self.model_name or model['model'] == self.model_name + ':latest' for model in models["models"])
            except Exception as e:
                logger.error(f"Model existence check failed: {e}")
                tries += 1
                # if tries >= 3:
                #     logger.error("Failed to check model existence after 3 attempts.")
                #     raise
                logger.info("Retrying in 30 seconds...")
                logger.debug(f"Retried {tries} times")
                time.sleep(30)