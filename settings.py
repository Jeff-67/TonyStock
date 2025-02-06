import enum
import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Model(str, enum.Enum):
    """Possible models."""

    claude_small = "claude-3-opus-20240229"
    claude_large = "claude-3-5-sonnet-latest"
    openai_small = "gpt-4o"
    openai_large = "o1"


class LogLevel(str, enum.Enum):
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


# flake8: noqa: E501
def get_opik_url_override(environment: str) -> None:
    """
    Set the OPIK URL override environment variable based on the environment.

    :param environment: The environment to set the override for.
    """
    if environment == "local":
        os.environ["OPIK_URL_OVERRIDE"] = os.getenv("OPIK_URL_OVERRIDE_LOCAL", "")
    if environment == "dev":
        os.environ["OPIK_URL_OVERRIDE"] = os.getenv("OPIK_URL_OVERRIDE_DEV", "")


class Settings(BaseSettings):
    """Application settings configuration."""

    log_level: LogLevel = LogLevel.INFO
    environment: str = "local"
    model: Model = Model.claude_large
    max_tokens: int = 8000

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        get_opik_url_override(self.environment)

    redis_config: dict = {
        "host": "127.0.0.1",
        "port": 6378,
        "db": 0,
        "password": os.getenv("REDIS_PASSWORD"),
        "max_connections": 10,
    }
    mongo_config: dict = {
        "uri": "mongodb://localhost:27017/",
        "db_name": os.getenv("MONGO_DATABASE"),
        "collection_name": os.getenv("MONGO_COLLECTION"),
        "username": os.getenv("MONGO_USERNAME"),
        "password": os.getenv("MONGO_PASSWORD"),
        "max_pool_size": 10,
    }
    mysql_config: dict = {
        "host": "127.0.0.1",
        "port": 3305,
        "username": "root",
        "password": os.getenv("MYSQL_ROOT_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }


settings = Settings()
