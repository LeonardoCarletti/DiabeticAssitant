from fastapi.testclient import TestClient
import sys
import os

# Adiciona o diretório raiz ao path para que possamos importar o backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Diabetics Assistant API is running!"}

def test_health_check():
    # Testa se pelo menos uma rota importante responde (mesmo que precise de auth, deve retornar 401 ou 403, não 500)
    response = client.get("/profile/logs")
    assert response.status_code in [200, 401, 403]
