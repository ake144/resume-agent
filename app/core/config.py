from dotenv import load_dotenv
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    groq_api_key: str
    database_url: str
    environment: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()