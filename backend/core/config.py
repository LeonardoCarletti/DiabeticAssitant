from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Diabetics Assistant API"

    # Banco de dados - use postgresql:// para Supabase na Vercel
    DATABASE_URL: str = "sqlite:///./diabetics.db"

    # APIs de IA
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Qdrant (vetor de embeddings)
    QDRANT_URL: str = "http://localhost:6333"

    # Firebase - modo 1: JSON como string (recomendado para Vercel)
    # Cole o conteudo completo do serviceAccount.json como valor desta variavel
    FIREBASE_SERVICE_ACCOUNT_JSON: Optional[str] = ""

    # Firebase - modo 2: caminho para arquivo (desenvolvimento local)
    FIREBASE_SERVICE_ACCOUNT_PATH: str = "firebase-service-account.json"

    class Config:
        env_file = ".env"

settings = Settings()
