# ============================================================
# BLOCO 5.3 — Conexão assíncrona com Supabase (Postgres)
# Arquivo: backend/database.py
# ============================================================

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("SUPABASE_DB_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")

# Pool otimizado para Serverless:
# pool_size=0 + NullPool evita conexões persistentes entre invocações
from sqlalchemy.pool import NullPool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # CRÍTICO para Vercel Serverless
    echo=False,          # True só em dev local para debug de SQL
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

class Base(DeclarativeBase):
    pass

# Dependency para injetar sessão nos handlers FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
