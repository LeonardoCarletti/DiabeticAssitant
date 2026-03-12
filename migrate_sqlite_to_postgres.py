import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.database import Base
from backend.models.user import (
    User, DailyLog, MedicalExam, ExamIndicator, NutritionLog, 
    WorkoutProgram, Exercise, WorkoutLog, Insight, RecoveryLog, Experiment
)
from backend.core.config import settings

def migrate():
    # 1. Configurar Engines
    sqlite_url = "sqlite:///./diabetics.db"
    postgres_url = settings.DATABASE_URL
    
    if "sqlite" in postgres_url:
        print("Erro: DATABASE_URL no seu .env ainda aponta para SQLite.")
        print("Por favor, instale o PostgreSQL e atualize seu .env conforme o guia.")
        return

    print(f"Iniciando migração: {sqlite_url} -> {postgres_url}")
    
    sqlite_engine = create_engine(sqlite_url)
    pg_engine = create_engine(postgres_url)
    
    # 2. Criar Tabelas no Postgres
    print("Criando esquema no PostgreSQL...")
    Base.metadata.create_all(pg_engine)
    
    # 3. Sessões
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PgSession = sessionmaker(bind=pg_engine)
    
    sqlite_db = SqliteSession()
    pg_db = PgSession()
    
    models = [
        User, DailyLog, MedicalExam, ExamIndicator, NutritionLog, 
        WorkoutProgram, Exercise, WorkoutLog, Insight, RecoveryLog, Experiment
    ]
    
    try:
        for model in models:
            table_name = model.__tablename__
            print(f"Migrando tabela: {table_name}...")
            
            # Buscar todos do SQLite
            items = sqlite_db.query(model).all()
            print(f"  - Encontrados {len(items)} registros.")
            
            for item in items:
                try:
                    # Criar uma nova instancia limpa para o Postgres
                    new_item = model()
                    
                    # Copiar todos os atributos que nao sao relacionamentos
                    for column in model.__table__.columns:
                        val = getattr(item, column.name)
                        
                        # Correção específica para IDs de usuários que podem vir como int do SQLite
                        if table_name == "users" and column.name == "id":
                            val = str(val)
                        
                        setattr(new_item, column.name, val)
                    
                    # Fazer o merge ou add
                    pg_db.merge(new_item)
                except Exception as e_item:
                    print(f"    - Erro no item: {e_item}")
                    raise e_item
            
            pg_db.commit()
            print(f"  - {table_name} migrada com sucesso!")
            
        print("\nMigracao concluida com sucesso! Agora o Diabetics Assistant eh Elite & Scalable.")
    except Exception as e:
        print(f"\nErro durante a migracao: {e}")
        pg_db.rollback()
    finally:
        sqlite_db.close()
        pg_db.close()

if __name__ == "__main__":
    migrate()
