from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Diabetics Assistant API"
    DATABASE_URL: str = "sqlite:///./diabetics.db" # Defaulting to SQLite for easy MVP, can upgrade to Postgre
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    QDRANT_URL: str = "http://localhost:6333"
    FIREBASE_SERVICE_ACCOUNT_PATH: str = "firebase-service-account.json"

    class Config:
        env_file = ".env"

settings = Settings()
