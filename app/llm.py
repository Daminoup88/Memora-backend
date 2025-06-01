import ollama
from config import logger, LLMSettings, clues_model_settings

class Model:
    def __init__(self, settings: LLMSettings):
        self.model_name = settings.model_name
        self.is_custom = settings.is_custom
        if not self.is_custom:
            self.pull_model_if_not_exists()
            return
        self.from_ = settings.from_
        self.parameters = settings.parameters
        self.template = settings.template
        self.system = settings.system
        self.create_model_if_not_exists()

    def manage_llm_errors(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ConnectionError as e:
                logger.error(f"Connection error: {e}")
            except Exception as e:
                logger.error(f"An error occurred: {e}")
        return wrapper

    @manage_llm_errors
    def create_model_if_not_exists(self):
        models = ollama.list()
        if any(model['model'] == self.model_name or model['model'] == self.model_name + ':latest' for model in models["models"]):
            logger.info(f"Model '{self.model_name}' already exists.")
        else:
            logger.info(f"Creating model '{self.model_name}'...")
            ollama.create(self.model_name, from_=self.from_, parameters=self.parameters, template=self.template, system=self.system)
            logger.info(f"Model '{self.model_name}' created successfully.")

    @manage_llm_errors
    def pull_model_if_not_exists(self):
        models = ollama.list()
        if any(model['model'] == self.model_name or model['model'] == self.model_name + ':latest' for model in models["models"]):
            logger.info(f"Model '{self.model_name}' already exists.")
        else:
            logger.info(f"Pulling model '{self.model_name}'...")
            ollama.pull(self.model_name)
            logger.info(f"Model '{self.model_name}' pulled successfully.")

test = Model(clues_model_settings)