from sqlalchemy import create_engine, text
from app.config import logger, settings

class Database:
    def __init__(self, database_name=None):
        if database_name is not None:
            settings.database_name = database_name
        self.create_database_if_not_exists()
        if settings.llm_enabled:
            self.create_vector_extension_if_not_exists()

    @property
    def DATABASE_URL(self):
        """Return the database URL."""
        return f"{settings.database_driver}://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"
    
    @property
    def DATABASE_SERVER(self):
        """Return the database URL without the database name."""
        return f"{settings.database_driver}://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/"

    def database_exists(self):
        """Check if the database already exists."""
        engine = create_engine(self.DATABASE_SERVER)
        with engine.connect() as connection:
            result = connection.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{settings.database_name}'"))
            return result.fetchone() is not None

    def create_database_if_not_exists(self): # pragma: no cover
        """Create the database if it does not exist."""
        try:
            if self.database_exists():
                logger.info(f"The database '{settings.database_name}' already exists.")
                return
            
            engine = create_engine(self.DATABASE_SERVER)
            with engine.connect() as connection:
                connection.execution_options(isolation_level="AUTOCOMMIT")
                query = text(f"CREATE DATABASE {settings.database_name}")
                connection.execute(query)
                logger.info(f"The database '{settings.database_name}' has been successfully created.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

    def create_vector_extension_if_not_exists(self): # pragma: no cover
        """Create the vector extension if it does not exist."""
        try:
            engine = create_engine(self.DATABASE_URL)
            with engine.connect() as connection:
                connection.execution_options(isolation_level="AUTOCOMMIT")
                query = text("CREATE EXTENSION IF NOT EXISTS vector")
                connection.execute(query)
                logger.info("The 'vector' extension has been successfully created if it did not exist.")
        except Exception as e:
            logger.error(f"An error occurred while creating the vector extension: {e}")
    
    def drop_database(self): # pragma: no cover
        """Drop the database."""
        try:
            engine = create_engine(self.DATABASE_SERVER)
            with engine.connect() as connection:
                connection.execution_options(isolation_level="AUTOCOMMIT")
                query = text(f"DROP DATABASE {settings.database_name}")
                connection.execute(query)
                logger.info(f"The database '{settings.database_name}' has been successfully dropped.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

database = Database()