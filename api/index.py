import sys
import os

# Adiciona o diretório raiz ao path para que possamos importar o backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.core.database import engine, Base
from backend.models import user  # noqa: F401 - importa modelos para criar tabelas

# Cria as tabelas no banco de dados ao iniciar (idempotente)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Erro ao criar tabelas: {e}")

# Vercel precisa que o objeto FastAPI seja exportado como 'app'
# e o arquivo deve ser nomeado de forma que o builder o encontre (ex: index.py)
