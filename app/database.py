import os
from sqlalchemy import create_engine, text
import json
from app.config import logger

class Database:
    def __init__(self, config_file="config.json"):
        """Initialize the database configuration."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, config_file)

        if not os.path.exists(config_path):
            default_config = {
                "db": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "postgres",
                    "password": "password",
                    "database": "database"
                }
            }
            with open(config_path, "w") as file:
                json.dump(default_config, file, indent=4)
                logger.info(f"Config file '{config_file}' has been created with the default values")

        with open(config_path) as config_file:
            config = json.load(config_file)

        db_config = config["db"]
        self.DB_SERVER = db_config["host"]
        self.DB_PORT = db_config["port"]
        self.DB_USER = db_config["user"]
        self.DB_PASSWORD = db_config["password"]
        self.DB_DATABASE = db_config["database"]
        self.create_database_if_not_exists()

    @property
    def DATABASE_URL(self):
        """Return the database URL."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_DATABASE}"

    def database_exists(self):
        """Check if the database already exists."""
        engine = create_engine(f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}:{self.DB_PORT}/")
        with engine.connect() as connection:
            result = connection.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{self.DB_DATABASE}'"))
            return result.fetchone() is not None

    def create_database_if_not_exists(self):
        """Create the database if it does not exist."""
        try:
            if self.database_exists():
                logger.info(f"The database '{self.DB_DATABASE}' already exists.")
                return
            
            engine = create_engine(f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}:{self.DB_PORT}/")
            with engine.connect() as connection:
                connection.execution_options(isolation_level="AUTOCOMMIT")
                query = text(f"CREATE DATABASE {self.DB_DATABASE}")
                connection.execute(query)
                logger.info(f"The database '{self.DB_DATABASE}' has been successfully created.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

database = Database()