import sys
import os

# Adiciona o diretório pai ao path para resolver imports 'from backend.api import ...'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
