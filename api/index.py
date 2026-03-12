import sys
import os

# Adiciona o diretório raiz ao path para que possamos importar o backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

# Vercel precisa que o objeto FastAPI seja exportado como 'app'
# e o arquivo deve ser nomeado de forma que o builder o encontre (ex: index.py)
