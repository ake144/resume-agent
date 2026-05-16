from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    database_url: str
    environment: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()