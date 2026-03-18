# backend/index.py
# Vercel Serverless Entrypoint
# Nome "index.py" evita conflito com o pacote "app/"

import sys
import os

# Garante que o diretorio backend esta no path
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app
