from ollama import AsyncClient, RequestError, ResponseError
from config import logger, LLMSettings
import asyncio
import sys
from functools import wraps
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class LLMModel(AsyncClient):
    def __init__(self, settings: LLMSettings):
        super().__init__()
        self.model_name = settings.model_name
        self.is_custom = settings.is_custom
        self.is_initialized = False
        if self.is_custom:
            self.from_ = settings.from_
            self.parameters = settings.parameters
            self.template = settings.template
            self.system = settings.system
    
    async def initialize(self):
        if self.is_initialized:
            return
        
        if not self.is_custom:
            await self.pull_model_if_not_exists()
        else:
            await self.create_model_if_not_exists()
        
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
        return async_wrapper

    @manage_llm_errors
    async def create_model_if_not_exists(self):
        models = await super().list()
        if any(model['model'] == self.model_name or model['model'] == self.model_name + ':latest' for model in models["models"]):
            logger.info(f"Model '{self.model_name}' already exists.")
        else:
            logger.info(f"Creating model '{self.model_name}'...")
            await super().create(self.model_name, from_=self.from_, parameters=self.parameters, template=self.template, system=self.system)
            logger.info(f"Model '{self.model_name}' created successfully.")

    @manage_llm_errors
    async def pull_model_if_not_exists(self):
        models = await super().list()
        if any(model['model'] == self.model_name or model['model'] == self.model_name + ':latest' for model in models["models"]):
            logger.info(f"Model '{self.model_name}' already exists.")
        else:
            logger.info(f"Pulling model '{self.model_name}'...")
            await super().pull(self.model_name)
            logger.info(f"Model '{self.model_name}' pulled successfully.")

    @manage_llm_errors
    async def generate(self, prompt: str, format: type[BaseModel] = None, **kwargs):
        if not self.is_initialized:
            await self.initialize()
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
        if not self.is_initialized:
            await self.initialize()
        kwargs['model'] = self.model_name
        response = await super().embed(input=prompt, **kwargs)
        return response['embeddings']